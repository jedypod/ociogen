###################################################################################################
# Super Minimal Pure-Python Colorimetry Functions
# 

def matmul(m0, m1):
	# multiply two square matrices
	return [[sum(a*b for a,b in zip(r, c)) for c in zip(*m1)] for r in m0]

def vdot(m, v):
	# multiply AxA matrix by Ax1 vector
	return [sum(x*y for x,y in zip(r,v)) for r in m]

def transpose(m):
	# transpose matrix m by swapping rows and cols
	return [list(r) for r in zip(*m)]

def zeros(s):
	# create square matrix of size s
	return [[0.0]*s for i in range(s)]

def identity(s):
	# return identity matrix of size s
	return diag(zeros(s), 1.0)

def is_identity(mtx):
	# Check if provided mtx matches identity matrix
	# rgb0_to_rgb1 = [round(e, 16) for r in rgb0_to_rgb1 for e in r]
	return all(abs(a - b) <= 1e-12 for row1, row2 in zip(mtx, identity(3)) for a, b in zip(row1, row2))

def diag(m, v):
	# set diagonal of matrix m to vector v or float v
	if isinstance(v, float):
		v = [v]*len(m)
	for p in range(len(m)):
		m[p][p] = v[p]
	return m

def flatten(m):
	# flatten multidimensional list m into 1D 
	return sum(m, [])

def pad_4x4(mtx):
	# pad 3x3 matrix to 4x4 then flatten
	if not isinstance(mtx, list):
		raise Exception(f'Error: need list to pad_4x4 - {mtx}')
	if len(mtx) == 9: # assume 1x9
		mtx = reshape(mtx)
	if (len(mtx) == 3 and len(mtx[0]) == 3):
		m = identity(4)
		for i in range(3):
			for j in range(3):
				m[i][j] = mtx[i][j]
		return flatten(m)
	else:
		raise Exception(f'Error: invalid list size to pad_4x4 - {mtx}')
	
def reshape(m, s=(3,3)):
	# reshape 1D list m into multidimensional list of shape (s,s)
	return [m[x:x+s[0]] for x in range(0, len(m), s[1])]

def det(m):
	# calculate determinant of 3x3 matrix m
	return m[0][0]*(m[1][1]*m[2][2]-m[2][1]*m[1][2])-m[0][1]*(m[1][0]*m[2][2]-m[1][2]*m[2][0])+m[0][2]*(m[1][0]*m[2][1]-m[1][1]*m[2][0])

def inv(m):
	# invert 3x3 matrix m
	if not len(m) == 3 and len(m[0]) == 3:
		print(f"Error: list is not of shape 3x3: {m}")
		return m
	d = det(m)
	if d == 0.0:
		print(f"Error: 3x3 matrix is not invertible: {m}")
		return m
	i = zeros(3)
	i[0][0] = (m[1][1]*m[2][2]-m[2][1]*m[1][2])/d
	i[0][1] = (m[0][2]*m[2][1]-m[0][1]*m[2][2])/d
	i[0][2] = (m[0][1]*m[1][2]-m[0][2]*m[1][1])/d
	i[1][0] = (m[1][2]*m[2][0]-m[1][0]*m[2][2])/d
	i[1][1] = (m[0][0]*m[2][2]-m[0][2]*m[2][0])/d
	i[1][2] = (m[1][0]*m[0][2]-m[0][0]*m[1][2])/d
	i[2][0] = (m[1][0]*m[2][1]-m[2][0]*m[1][1])/d
	i[2][1] = (m[2][0]*m[0][1]-m[0][0]*m[2][1])/d
	i[2][2] = (m[0][0]*m[1][1]-m[1][0]*m[0][1])/d
	return i

def npm(ch):
	# Calculate the Normalized Primaries Matrix for the specified chromaticities ch
	# ch is a 2x4 or 1x8 matrix specifying xy chromaticity coordinates for R G B and W
  # Adapted from SMPTE Recommended Practice - Derivation of Basic Television Color Equations
  # http://doi.org/10.5594/S9781614821915
	if len(ch) == 8: # handle flat list
		ch = [[ch[0], ch[1]], [ch[2], ch[3]], [ch[4], ch[5]], [ch[6], ch[7]]]
	for c in ch:
		c.append(1.0-c[0]-c[1])
	P = transpose([ch[0], ch[1], ch[2]])
	W = [ch[3][0] / ch[3][1], 1.0, ch[3][2] / ch[3][1]]
	C = vdot(inv(P), W)
	C = diag(zeros(3), C)
	return matmul(P, C)

def wp(ch):
	# return whitepoint of chromaticities array ch
	return ch[-2:]

def xy_to_XYZ(xy):
	# convert xy chromaticity to XYZ tristimulus with Y=1.0
	return [xy[0]/xy[1], 1.0, (1.0-xy[0]-xy[1])/xy[1]]

def cat(ws, wd, method='cat02'):
	# Calculate a von Kries style chromatic adaptation transform matrix given xy chromaticities
	# for src white (ws) and dst white (wd)
  # Source: Mark D. Fairchild - 2013 - Color Appearance Models Third Edition p. 181-186
  # Source: Bruce Lindbloom - Chromatic Adaptation - http://www.brucelindbloom.com/index.html?Eqn_ChromAdapt.html
	if ws == wd: # src and dst are equal, nothing to do
		return identity(3)
	if method == 'bradford':
		mcat = [[0.8951, 0.2664, -0.1614], [-0.7502, 1.7135, 0.0367], [0.0389, -0.0685, 1.0296]]
	elif method == 'cat02':
		mcat = [[0.7328, 0.4296, -0.1624], [-0.7036, 1.6975, 0.0061], [0.003, 0.0136, 0.9834]]
	else:
		mcat = identity(3)
	sXYZ = xy_to_XYZ(ws)
	dXYZ = xy_to_XYZ(wd)
	s_cone_mtx = vdot(mcat, sXYZ)
	d_cone_mtx = vdot(mcat, dXYZ)
	smat = diag(zeros(3), [a/b for a,b in zip(d_cone_mtx, s_cone_mtx)])
	nmtx = matmul(inv(mcat), smat)
	return matmul(nmtx, mcat)

def rgb_to_xyz_cat(ch, wdst, method='cat02'):
	# Calculate an RGB to XYZ Normalized Primaries Matrix, with CAT to wdst whitepoint
	rgb_to_xyz = npm(ch)
	cat_mtx = cat(wp(ch), wdst, method=method)
	return matmul(cat_mtx, rgb_to_xyz)

def rgb_to_rgb(ch0, ch1, cat_method='cat02'):
	# Wrapper function to calculate a 3x3 matrix to convert from RGB gamut ch0 to RGB gamut ch1
	# including chromatic adaptation transform.
	rgb0_to_xyz = npm(ch0)
	rgb1_to_xyz = npm(ch1)
	xyz_to_cat = cat(wp(ch0), wp(ch1), method=cat_method)
	rgb0_to_cat = matmul(xyz_to_cat, rgb0_to_xyz)
	rgb0_to_rgb1 = matmul(inv(rgb1_to_xyz), rgb0_to_cat)
	# rgb0_to_rgb1 = [round(e, 16) for r in rgb0_to_rgb1 for e in r]
	return rgb0_to_rgb1


__all__ = [
	"cat", "det", "diag", "flatten", "inv", "identity",
	"is_identity", "matmul", "npm", "pad_4x4", "reshape",
	"rgb_to_rgb", "rgb_to_xyz_cat", "transpose", "vdot",
	"wp", "xy_to_XYZ", "zeros"
]