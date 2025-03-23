import os
import re
import itertools
import PyOpenColorIO as ocio

from .colorimetry import *


def linspace(mn, mx, cnt):
	# return evenly spaced list of cnt numbers between mn and mx, including mx
	assert isinstance(cnt, int) and (cnt > 2)
	step = (mx - mn) / float(cnt-1)
	return itertools.islice(itertools.count(mn, step), cnt)


def gen_spi1d(fn, lut_path, inv=False, mn=0.0, mx=1.0, LUT_SIZE=2**14):
	# generate a 1D LUT as an spi1d file, given a function fn
	y = [str(round(fn(x, inv=inv), 9)) for x in linspace(mn, mx, LUT_SIZE)]
	# print(f'{lut_path}\n{y[:5]} ... {y[-5:]}')
	contents = f'Version 1\nFrom {mn} {mx}\nLength {LUT_SIZE}\nComponents 1\n{{\n'
	contents += '\n'.join(y)
	contents += '\n}'
	with open(lut_path, 'w') as f:
		f.write(contents)
	if not os.path.isfile(lut_path):
		raise(Exception)


def ocio_xform_camera_log(lg_o, lg_s, ln_o, ln_s, ln_brk, ln_sl=None):
	''' Helper function to create an OCIO Camera Transform in the log to lin (TO_REFERENCE) direction
			Who wrote this syntax >:/
	'''
	xform = ocio.LogCameraTransform(
		linSideBreak=[ln_brk]*3,
		logSideSlope=[lg_s]*3,
		logSideOffset=[lg_o]*3,
		linSideSlope=[ln_s]*3,
		linSideOffset=[ln_o]*3,
		direction=ocio.TransformDirection.TRANSFORM_DIR_INVERSE)
	if ln_sl:
		xform.setLinearSlopeValue([ln_sl]*3)
	return xform

def ocio_xform_log(lg_o, lg_s, ln_o, ln_s):
	''' Helper function to create an OCIO Camera Transform in the log to lin (TO_REFERENCE) direction
			Who wrote this syntax >:/
	'''
	return ocio.LogAffineTransform(
		logSideSlope=[lg_s]*3,
		logSideOffset=[lg_o]*3,
		linSideSlope=[ln_s]*3,
		linSideOffset=[ln_o]*3,
		direction=ocio.TransformDirection.TRANSFORM_DIR_INVERSE)

def ocio_xform_expln(g, o, inv=True):
	'''OCIO ExponentWithLinear transform.
			For some unknown reason if the constructor is used, there is an exception
			complaining about upper or lower bounds... no idea. Thus the weird structure.
	'''
	direction = ocio.TransformDirection.TRANSFORM_DIR_INVERSE if inv else ocio.TransformDirection.TRANSFORM_DIR_FORWARD
	xform = ocio.ExponentWithLinearTransform()
	xform.setDirection(direction)
	# xform.setGamma([g, g, g, 1.0])
	# xform.setOffset([o, o, o, 1.0])
	xform.setGamma([g, g, g, g])
	xform.setOffset([o, o, o, o])
	return xform

def ocio_xform_exp(p, inv=True):
	''' OCIO ExponentTransform
	'''
	direction = ocio.TransformDirection.TRANSFORM_DIR_INVERSE if inv else ocio.TransformDirection.TRANSFORM_DIR_FORWARD
	return ocio.ExponentTransform(
		value=[p, p, p, 1.0],
		direction=direction,
		)

def ocio_xform_builtin(style, inv=True):
	''' OCIO BuiltinTransform
	'''
	direction = ocio.TransformDirection.TRANSFORM_DIR_INVERSE if inv else ocio.TransformDirection.TRANSFORM_DIR_FORWARD
	return ocio.BuiltinTransform(style=style, direction=direction)


def unbloat(cfg):
	# strip useless colorspace defaults bloating the config
	cfg = cfg.replace('equalitygroup: ""\n    ', '') # unspecified equalitygroup is unecessary
	cfg = cfg.replace('isdata: false\n    ', '') # isdata: false is the default.
	cfg = cfg.replace('allocation: uniform\n    ', '') # uniform 0-1 allocation is default.
	cfg = cfg.replace('allocation: uniform\n', '') # uniform 0-1 allocation is default.
	cfg = cfg.replace('allocationvars: [0, 1]\n    ', '') # uniform 0-1 allocation is default.
	cfg = cfg.replace('bitdepth: 32f\n    ', '') # bitdepth 32f is the default https://opencolorio.readthedocs.io/en/rb-1.1/userguide/config_syntax.html#bitdepth
	return cfg


def create_ocio_colorspace(c, reference, ocio_version_major, config_dir, LUT_SIZE=2**15):
	''' Create and return an OCIO Colorspace, given a Colorspace dataclass object `c`
	'''
	print(f"Setting up colorspace: {c.name}")

	#  Colorspace Allocation
	# 		For scene-linear colorspaces, we need to define allocation for the colorspace,
	# 		which specifies how to distribute values in the colorspace on the GPU. 
	# 		OCIO uses a log base 2 allocation, defined by a list: [min, max, offset], where min is 2^min, 
	# 		max is 2^max and offset is a float offset value so we can represent values at 0.0 and below.
	# 		To calculate this we define a desired scene-linear min value and max value, and then calculate 
	# 		the appropriate values for the allocation.
	# gpu_linear_min = -0.005
	# gpu_linear_max = 256.0
	
	# lg2_min = -10
	# lg2_offset = round(2**lg2_min - gpu_linear_min, 4) # trade off exactitude for a clean number in allocationvars offset
	# import math
	# lg2_max = math.log2(gpu_linear_max)
	# GPU_ALLOCATIONVARS = [lg2_min, lg2_max, lg2_offset]
	# print(f'lin min: {gpu_linear_min}\nlg2_min {2**lg2_min}\nlg2_offset {lg2_offset}\n actual linear min: {2**lg2_min - lg2_offset}\n linear max {2**lg2_max}')
	# print(f'ALLOC: [{lg2_min}, {lg2_max}, {lg2_offset}]')

	GPU_ALLOCATIONVARS = [-10, 8.0, 0.006] # Covers linear range of ~-0.005 to 256.0
	
	# Set up basic parameters of the OCIO Colorspace object.
	cs = ocio.ColorSpace()
	cs.setName(c.name)
	if ocio_version_major >= 2:
		cs.addAlias(c.alias)
	cs.setDescription(c.desc)
	cs.setFamily(c.family)
	cs.setBitDepth(ocio.BIT_DEPTH_F32)
	
	direction = ocio.COLORSPACE_DIR_TO_REFERENCE if c.forward else ocio.COLORSPACE_DIR_FROM_REFERENCE
	
	# list of transforms to be applied
	xforms = []

	# Transfer Functions
	if c.tf:
		if callable(c.tf):
			# Create spi1d from python function
			lut_filename = f'{c.tf.__name__}_to_linear.spi1d'
			lut_dir = os.path.join(config_dir, 'luts')
			if not os.path.isdir(lut_dir):
				os.makedirs(lut_dir)
			lut_filepath = os.path.join(lut_dir, lut_filename)
			if 'oetf' in c.tf.__name__:
				gen_spi1d(c.tf, lut_filepath, mn=-0.15, mx=1.2, inv=True, LUT_SIZE=LUT_SIZE)
			elif 'eotf' in c.tf.__name__ or 'eocf' in c.tf.__name__:
				gen_spi1d(c.tf, lut_filepath, mn=0.0, mx=1.2, inv=False, LUT_SIZE=LUT_SIZE)
			xforms.append(ocio.FileTransform(lut_filename))
		elif isinstance(c.tf, ocio.Transform):
			xforms.append(c.tf)

	# Gamut Conversions
	if isinstance(c.chr, list):
		# Convert RGBW xy Chromaticities into 3x3 matrix which converts to Reference Gamut
		mtx = rgb_to_rgb(c.chr, reference.chr)
		if not is_identity(mtx):
			# print(f'chr: {c.chr} -> {mtx}')
			xforms.append(ocio.MatrixTransform(pad_4x4(mtx)))
	elif isinstance(c.chr, str):
		# gamut conversion is a reference to another linear colorspace (avoids multiple duplicate MatrixTransforms)
		if c.forward:
			xforms.append(ocio.ColorSpaceTransform(src=c.chr, dst='reference'))
		else:
			xforms.append(ocio.ColorSpaceTransform(src='reference', dst=c.chr))

	if len(xforms) == 1:
		# single transform Linear colorspace
		cs.setTransform(xforms[0], direction=direction)
		if ocio_version_major < 2:
			# If linear colorspace, needs LG2 allocation
			cs.setAllocation(ocio.ALLOCATION_LG2)
			cs.setAllocationVars(GPU_ALLOCATIONVARS)
	elif len(xforms) > 1:
		if not c.forward:
			xforms = xforms[::-1] # reverse order
		# group transform required
		grp_xform = ocio.GroupTransform()
		for xform in xforms:
			grp_xform.appendTransform(xform)
		cs.setTransform(grp_xform, direction=direction)
	else:
		print(f'Warning! No transforms defined for this colorspace, setting {c.name} as the reference space!')

	# Set Encoding if OCIOv2
	if c.encoding != '' and ocio_version_major > 1:
		valid_encodings = ['scene-linear', 'log', 'sdr-video', 'hdr-video', 'data']
		if c.encoding in valid_encodings:
			cs.setEncoding(c.encoding)

	return cs