from dataclasses import dataclass
from inspect import getmembers, isfunction
import PyOpenColorIO as ocio

from . import transfer_functions
from .ocio_utility_functions import *


@dataclass
class Colorspace:
	name: str # Colorspace name.
	alias: str # Aliases for this colorspace (OCIO V2 ONLY!)
	desc: str = '' # Colorspace description
	family: str = '' # Colorspace family
	encoding: str = '' # Colorspace encoding: scene-linear, log, sdr-video, hdr-video, data (OCIO V2 ONLY!)
	chr: object = None # 1x8 list of RGBW xy chromaticities, or string for another colorspace
	tf: object = None # Colorspace transfer function: a python method or an OCIO object, or None if linear
	forward: bool = True # forward is the TO_REFERENCE direction, otherwise FROM_REFERENCE



def get_colorspaces(OCIOv):
	''' ##################################################################
			# Colorspace Definitions
			##################################################################
	'''
	# Assemble dict of all transfer function methods from transfer_functions module
	# then layer over the same transfer functions with ocio v2 transforms, if we have access to ocio v2
	tfuncs = {}
	for nm, fn in getmembers(transfer_functions, isfunction):
		tfuncs[nm] = fn

	if OCIOv >= 2.0:
		# If we have OCIO version 2.0 or above, replace spi1d luts with camera log transforms, where possible.
		# Calculations: https://colab.research.google.com/drive/1rVuaYy63PcO5GynvGLh9Y8VPre8bRP88
		tfuncs['oetf_acescct'] = ocio_xform_camera_log(0.554794520547945, 0.0570776255707763, 0.0, 1.0, 0.0078125)
		tfuncs['oetf_filmlight_tlog'] = ocio_xform_camera_log(0.5520126568606655, 0.0639976040320219, 0.0057048244042473785, 1.0, 0.0)
		tfuncs['oetf_davinci_intermediate'] = ocio_xform_camera_log(0.51304736, 0.07329248, 0.0075, 1.0, 0.00262409)
		tfuncs['oetf_arri_logc3'] = ocio_xform_camera_log(0.385537, 0.0744116046281795, 0.052272, 5.555556, 0.010591)
		tfuncs['oetf_arri_logc4'] = ocio_xform_camera_log(-0.295908392682586, 0.0647954196341293, 64, 2231.82630906769, -0.01805699611991131)
		tfuncs['oetf_blackmagic_bmdfilmgen5'] = ocio_xform_camera_log(0.5300133392291939, 0.06025442535752273, 0.005494072432257808, 1, 0.005)
		tfuncs['oetf_canon_clog2'] = ocio_xform_camera_log(0.092864125, 0.07265683154655515, 1, 96.77708333333334, 0.0)
		tfuncs['oetf_kodak_cineon'] = ocio_xform_log(0.669599217986315, 0.08827859110380668, 0.0107977516232771, 0.989202248376723)
		tfuncs['oetf_dji_dlog'] = ocio_xform_camera_log(0.584555, 0.07726326177710438, 0.0108, 0.9892, 0.0078, ln_sl=6.025)
		tfuncs['oetf_fujifilm_flog'] = ocio_xform_camera_log(0.790453, 0.10375781478547835, 0.009468, 0.555556, 0.00089, ln_sl=8.735631)
		tfuncs['oetf_fujifilm_flog2'] = ocio_xform_camera_log(0.384316, 0.07383693836645695, 0.064829, 5.555556, 0.000889, ln_sl=8.799461)
		tfuncs['oetf_gopro_protune'] = ocio_xform_camera_log(0.0, 0.14662371845531116, 1.0, 112.0, 0.0)
		tfuncs['oetf_leica_llog'] = ocio_xform_camera_log(0.6, 0.08127809882927492, 0.0115, 1.3, 0.006, ln_sl=8.0)
		tfuncs['oetf_panasonic_vlog'] = ocio_xform_camera_log(0.598206, 0.07270295837279074, 0.00873, 1, 0.01)
		tfuncs['oetf_red_log3g10'] = ocio_xform_camera_log(0, 0.06751560948750902, 2.55975327, 155.975327, -0.01)
		tfuncs['oetf_sony_slog2'] = ocio_xform_camera_log(0.616244473118279, 0.111538329628718, 0.037584, 0.786402841197362, 0.0, ln_sl=3.53881278538813)
		tfuncs['oetf_sony_slog3'] = ocio_xform_camera_log(0.410557184750733, 0.07694950524548466, 0.0526315789473684, 5.26315789473684, 0.01125, ln_sl=6.62194371177582)
		tfuncs['oetf_jplog2'] = ocio_xform_camera_log(0.513196480938416, 0.0488758553274682, 0, 1, 0.006801176276)
		tfuncs['eotf_st2084'] = ocio_xform_builtin('CURVE - ST-2084_to_LINEAR')
		# tfuncs['eotf_hlg'] = ocio_xform_builtin('CURVE - HLG-OETF')
		tfuncs['eocf_srgb'] = ocio_xform_expln(2.4, 0.055)
		tfuncs['eocf_rec709'] = ocio_xform_expln(2.22222222222222, 0.099)


	# Colorspace Definitions
	working_colorspaces = [
		
		# Scene-Referred Working Colorspaces
		Colorspace(
			name = 'raw',
			alias = 'nc',
			desc = 'Non-Color Data',
			family = 'Scene-Referred/Utility',
			encoding = 'data',
		),
		Colorspace(
			name = 'XYZ D65',
			alias = 'xyzd65',
			desc = 'Linear CIE XYZ adapted to the Illuminant D65 whitepoint',
			family = 'Scene-Referred/Utility',
			encoding = 'scene-linear',
			chr = [1, 0, 0, 1, 0, 0, 0.3127, 0.329],
		),
		Colorspace(
			name = 'XYZ E',
			alias = 'xyze',
			desc = 'Linear CIE XYZ adapted to the Illuminant E whitepoint',
			family = 'Scene-Referred/Utility',
			encoding = 'scene-linear',
			chr = [1, 0, 0, 1, 0, 0, 1.0/3.0, 1.0/3.0],
		),
		Colorspace(
			name = 'ACES 2065-1',
			alias = 'ap0',
			desc = 'Linear AP0 ACES 2065-1\nTB-2014-004 : Informative Notes on SMPTE ST 2065-1 - Academy Color Encoding Specification (ACES)\nhttp://j.mp/TB-2014-004',
			family = 'Scene-Referred/ACES',
			encoding = 'scene-linear',
			chr = [0.7347, 0.2653, 0.0, 1.0, 0.0001, -0.077, 0.32168, 0.33767],
		),
		Colorspace(
			name = 'ACEScg',
			alias = 'ap1',
			desc = 'Linear AP1 ACEScg\nS-2014-004 : ACEScg — A Working Space for CGI Render and Compositing\nhttp://j.mp/S-2014-004',
			family = 'Scene-Referred/ACES',
			encoding = 'scene-linear',
			chr = [0.713, 0.293, 0.165, 0.83, 0.128, 0.044, 0.32168, 0.33767],
		),
		Colorspace(
			name = 'ACEScct',
			alias = 'acescct',
			desc = 'ACES AP1 - ACEScct Log\nS-2016-001 : ACEScct — A Quasi-Logarithmic Encoding of ACES Data for use within Color Grading Systems\nhttp://j.mp/S-2016-001_',
			family = 'Scene-Referred/ACES',
			encoding = 'log',
			chr = 'ACEScg',
			tf = tfuncs.get('oetf_acescct'),
		),
		Colorspace(
			name = 'Filmlight - E-Gamut - Linear',
			alias = 'fegln',
			desc = 'Filmlight E-Gamut - Linear\nSpecified in the flspace file included with the Baselight software\n/etc/colourspaces/FilmLight_Linear_EGamut.flspace',
			family = 'Scene-Referred/Filmlight',
			encoding = 'scene-linear',
			chr = [0.8, 0.3177, 0.18, 0.9, 0.065, -0.0805, 0.3127, 0.329],
		),
		Colorspace(
			name = 'Filmlight - E-Gamut - T-Log',
			alias = 'feglg',
			desc = 'Filmlight E-Gamut - T-Log\nSpecified in the flspace file included with the Baselight software\n/etc/colourspaces/FilmLight_TLog_EGamut.flspace',
			family = 'Scene-Referred/Filmlight',
			encoding = 'log',
			chr = 'Filmlight - E-Gamut - Linear',
			tf = tfuncs.get('oetf_filmlight_tlog'),
		),
		Colorspace(
			name = 'Filmlight - E-Gamut2 - Linear',
			alias = 'feg2ln',
			desc = 'Filmlight E-Gamut2 - Linear\nSpecified in the flspace file included with the Baselight software\n/etc/colourspaces/FilmLight_Linear_EGamut2.flspace',
			family = 'Scene-Referred/Filmlight',
			encoding = 'scene-linear',
			chr = [0.83, 0.31, 0.15, 0.95, 0.065, -0.0805, 0.3127,0.329],
		),
		Colorspace(
			name = 'Filmlight - E-Gamut2 - T-Log',
			alias = 'feg2lg',
			desc = 'Filmlight E-Gamut2 - T-Log\nSpecified in the flspace file included with the Baselight software\n/etc/colourspaces/FilmLight_Linear_EGamut2.flspace',
			family = 'Scene-Referred/Filmlight',
			encoding = 'log',
			chr = 'Filmlight - E-Gamut2 - Linear',
			tf = tfuncs.get('oetf_filmlight_tlog'),
		),
		Colorspace(
			name = 'DaVinci - WideGamut - Linear',
			alias = 'dwgln',
			desc = 'DaVinci Wide Gamut - Linear\nhttps://documents.blackmagicdesign.com/InformationNotes/DaVinci_Resolve_17_Wide_Gamut_Intermediate.pdf',
			family = 'Scene-Referred/Blackmagic Design',
			encoding = 'scene-linear',
			chr = [0.8, 0.313, 0.1682, 0.9877, 0.079, -0.1155, 0.3127, 0.329],
		),
		Colorspace(
			name = 'DaVinci - WideGamut - Intermediate Log',
			alias = 'dwglg',
			desc = 'Davinci Wide Gamut - Intermediate Log',
			family = 'Scene-Referred/Blackmagic Design',
			encoding = 'log',
			chr = 'DaVinci - WideGamut - Linear',
			tf = tfuncs.get('oetf_davinci_intermediate'),
		),
	]

	camera_colorspaces = [
		# Scene-Referred Camera Colorspaces
		Colorspace(
			name = 'Arri - WideGamut - Linear',
			alias = 'awgln',
			desc = 'Arri Wide Gamut - Linear\nhttps://www.arri.com/resource/blob/31918/66f56e6abb6e5b6553929edf9aa7483e/2017-03-alexa-logc-curve-in-vfx-data.pdf',
			family = 'Scene-Referred/Arri',
			encoding = 'scene-linear',
			chr = [0.684, 0.313, 0.221, 0.848, 0.0861, -0.102, 0.3127, 0.329],
		),
		Colorspace(
			name = 'Arri - WideGamut - LogC3',
			alias = 'awglg',
			desc = 'Arri Wide Gamut - LogCv3 EI800',
			family = 'Scene-Referred/Arri',
			encoding = 'log',
			chr = 'Arri - WideGamut - Linear',
			tf = tfuncs.get('oetf_arri_logc3'),
		),
		Colorspace(
			name = 'Arri - WideGamut4 - Linear',
			alias = 'awg4ln',
			desc = 'Arri Wide Gamut 4 - Linear\nhttps://www.arri.com/resource/blob/278790/bea879ac0d041a925bed27a096ab3ec2/2022-05-arri-logc4-specification-data.pdf',
			family = 'Scene-Referred/Arri',
			encoding = 'scene-linear',
			chr = [0.7347, 0.2653, 0.1424, 0.8576, 0.0991, -0.0308, 0.3127, 0.329],
		),
		Colorspace(
			name = 'Arri - WideGamut4 - LogC4',
			alias = 'awg4lg',
			desc = 'Arri Wide Gamut 4 - LogC4',
			family = 'Scene-Referred/Arri',
			encoding = 'log',
			chr = 'Arri - WideGamut4 - Linear',
			tf = tfuncs.get('oetf_arri_logc4'),
		),
		Colorspace(
			name = 'Blackmagic - WideGamut - Linear',
			alias = 'bwgln',
			desc = 'Blackmagic Camera Wide Gamut - Linear\nSpecified in the Blackmagic Generation 5 Color Science whitepaper included in the Blackmagic Raw SDK available here\nhttps://www.blackmagicdesign.com/support/download/1bad3dc74c2c4a908ce5c9ce8b9f74f8/Linux\n/usr/lib64/blackmagic/BlackmagicRAWSDK/Documents/Blackmagic Generation 5 Color Science Technical Reference.pdf',
			family = 'Scene-Referred/Blackmagic Design',
			encoding = 'scene-linear',
			chr = [0.7177215, 0.3171181, 0.228041, 0.861569, 0.1005841, -0.0820452, 0.3127, 0.329],
		),
		Colorspace(
			name = 'Blackmagic - WideGamut - Blackmagic Film Gen5 Log',
			alias = 'bwglg',
			desc = 'Blackmagic Wide Gamut - Blackmagic Film Generation 5 Log (OETF)',
			family = 'Scene-Referred/Blackmagic Design',
			encoding = 'log',
			chr = 'Blackmagic - WideGamut - Linear',
			tf = tfuncs.get('oetf_blackmagic_bmdfilmgen5'),
		),
		Colorspace(
			name = 'Canon - Cinema Gamut - Linear',
			alias = 'ccgln',
			desc = 'Canon Cinema Gamut - Linear\nNote - this is the D55 daylight IDT matrix not the Tungsten IDT\nCanon Cinema Gamut primaries specified on this marketing article for the Canon C500\nhttps://www.usa.canon.com/internet/portal/us/home/explore/product-showcases/cameras-and-lenses/cinema-eos-firmware/c500\n\nFrom https://www.usa.canon.com/internet/portal/us/home/support/details/cameras/cinema-eos/eos-c300-mark-iii-digital-cinema-camera/eos-c300-mark-iii-digital-cinema-camera?tab=drivers_downloads\nInput Transform Version 202007 for EOS C300 Mark III - canon-eos-c300mk3-idt-202007.zip',
			family = 'Scene-Referred/Canon',
			encoding = 'scene-linear',
			chr = [0.74, 0.27, 0.17, 1.14, 0.08, -0.1, 0.3127, 0.329],
		),
		Colorspace(
			name = 'Canon - Cinema Gamut - C-Log2',
			alias = 'ccglg',
			desc = 'Canon CLog2\nCLog2 is intended for grading workflows, whereas CLog3 is intended for a more "direct to display" workflow.\n\nCanon log transfer functions are all described in this whitepaper:\nhttps://downloads.canon.com/nw/learn/white-papers/cinema-eos/white-paper-canon-log-gamma-curves.pdf\n\nThe log transfer functions described above match the 1D LUTs available in the "Canon lookup table Version 201911" \ndownload available here\nhttps://www.usa.canon.com/internet/portal/us/home/support/details/cameras/cinema-eos/cinema-eos-c500-mark-ii?tab=drivers_downloads\n\nHowever in the CTL ACES IDT provided in the "Input Transform Version 202007 for EOS C500 Mark II" file \nat the above url, they add the /=0.9 on the scene-linear values. This function matches the IDT.',
			family = 'Scene-Referred/Canon',
			encoding = 'log',
			chr = 'Canon - Cinema Gamut - Linear',
			tf = tfuncs.get('oetf_canon_clog2'),
		),
		Colorspace(
			name = 'DJI - D-Gamut - Linear',
			alias = 'dgln',
			desc = 'DJI D-Gamut - Linear\nhttps://dl.djicdn.com/downloads/zenmuse+x7/20171010/D-Log_D-Gamut_Whitepaper.pdf',
			family = 'Scene-Referred/DJI',
			encoding = 'scene-linear',
			chr = [0.71, 0.31, 0.21, 0.88, 0.09, -0.08, 0.3127, 0.329],
		),
		Colorspace(
			name = 'DJI - D-Gamut - D-Log',
			alias = 'dglg',
			desc = 'DJI D-Gamut - D-Log',
			family = 'Scene-Referred/DJI',
			encoding = 'log',
			chr = 'DJI - D-Gamut - Linear',
			tf = tfuncs.get('oetf_dji_dlog'),
		),
		Colorspace(
			name = 'Fujifilm - F-Gamut - Linear',
			alias = 'fgln',
			desc = 'Fujifilm F-Gamut - Linear\nNote - F-Gamut is identical to Rec.2020\nhttps://dl.fujifilm-x.com/support/lut/F-Log_DataSheet_E_Ver.1.0.pdf',
			family = 'Scene-Referred/Fujifilm',
			encoding = 'scene-linear',
			chr = [0.708, 0.292, 0.17, 0.797, 0.131, 0.046, 0.3127, 0.329],
		),
		Colorspace(
			name = 'Fujifilm - F-Gamut - F-Log',
			alias = 'fglg',
			desc = 'Fujifilm F-Gamut - F-Log',
			family = 'Scene-Referred/Fujifilm',
			encoding = 'log',
			chr = 'Fujifilm - F-Gamut - Linear',
			tf = tfuncs.get('oetf_fujifilm_flog'),
		),
		Colorspace(
			name = 'Fujifilm - F-Gamut - F-Log2',
			alias = 'fglg2',
			desc = 'Fujifilm F-Gamut - F-Log2',
			family = 'Scene-Referred/Fujifilm',
			encoding = 'log',
			chr = 'Fujifilm - F-Gamut - Linear',
			tf = tfuncs.get('oetf_fujifilm_flog2'),
		),
		Colorspace(
			name = 'Fujifilm - F-GamutC - Linear',
			alias = 'fgcln',
			desc = 'Fujifilm F-GamutC - Linear\nhttps://dl.fujifilm-x.com/support/lut/F-Log2C_DataSheet_E_Ver.1.0.pdf',
			family = 'Scene-Referred/Fujifilm',
			encoding = 'scene-linear',
			chr = [0.7347, 0.2653, 0.0263, 0.9737, 0.1173, -0.0224, 0.3127, 0.329],
		),
		Colorspace(
			name = 'Fujifilm - F-GamutC - F-Log2',
			alias = 'fgclg2',
			desc = 'Fujifilm F-GamutC - F-Log2',
			family = 'Scene-Referred/Fujifilm',
			encoding = 'log',
			chr = 'Fujifilm - F-GamutC - Linear',
			tf = tfuncs.get('oetf_fujifilm_flog2'),
		),
		Colorspace(
			name = 'Leica - Rec.2020 - Linear',
			alias = 'llgln',
			desc = 'Leica Rec.2020 - Linear\n',
			family = 'Scene-Referred/Leica',
			encoding = 'scene-linear',
			chr = [0.708, 0.292, 0.17, 0.797, 0.131, 0.046, 0.3127, 0.329],
		),
		Colorspace(
			name = 'Leica - Rec.2020 - L-Log',
			alias = 'llglg',
			desc = 'Leica Rec.2020 - L-Log\nhttps://leica-camera.com/sites/default/files/pm-65977-210914__L-Log_Reference_Manual_EN.pdf',
			family = 'Scene-Referred/Leica',
			encoding = 'log',
			chr = 'Leica - Rec.2020 - Linear',
			tf = tfuncs.get('oetf_leica_llog'),
		),
		Colorspace(
			name = 'Panasonic - V-Gamut - Linear',
			alias = 'vgln',
			desc = 'Panasonic V-Gamut - Linear\nhttps://pro-av.panasonic.net/en/cinema_camera_varicam_eva/support/pdf/VARICAM_V-Log_V-Gamut.pdf',
			family = 'Scene-Referred/Panasonic',
			encoding = 'scene-linear',
			chr = [0.73, 0.28, 0.165, 0.84, 0.1, -0.03, 0.3127, 0.329],
		),
		Colorspace(
			name = 'Panasonic - V-Gamut - V-Log',
			alias = 'vglg',
			desc = 'Panasonic V-Gamut - V-Log',
			family = 'Scene-Referred/Panasonic',
			encoding = 'log',
			chr = 'Panasonic - V-Gamut - Linear',
			tf = tfuncs.get('oetf_panasonic_vlog'),
		),
		Colorspace(
			name = 'Red - WideGamutRGB - Linear',
			alias = 'rwgln',
			desc = 'Red Wide Gamut RGB - Linear\nhttps://docs.red.com/955-0187/PDF/915-0187%20Rev-C%20%20%20RED%20OPS,%20White%20Paper%20on%20REDWideGamutRGB%20and%20Log3G10.pdf',
			family = 'Scene-Referred/Red',
			encoding = 'scene-linear',
			chr = [0.780308, 0.304253, 0.121595, 1.493994, 0.095612, -0.084589, 0.3127, 0.329],
		),
		Colorspace(
			name = 'Red - WideGamutRGB - Log3G10',
			alias = 'rwglg',
			desc = 'Red Wide Gamut RGB - Log3G10',
			family = 'Scene-Referred/Red',
			encoding = 'log',
			chr = 'Red - WideGamutRGB - Linear',
			tf = tfuncs.get('oetf_red_log3g10'),
		),
		Colorspace(
			name = 'Sony - S-Gamut3 - Linear',
			alias = 'sg3ln',
			desc = 'Sony S-Gamut3 - Linear\nNote: S-Gamut and S-Gamut3 have identical primaries. \nThey are described as more of a camera negative colorspace than a grading space in the whitepaper.\nhttps://pro.sony/s3/cms-static-content/uploadfile/06/1237494271406.pdf',
			family = 'Scene-Referred/Sony',
			encoding = 'scene-linear',
			chr = [0.73, 0.28, 0.14, 0.855, 0.1, -0.05, 0.3127, 0.329],
		),
		Colorspace(
			name = 'Sony - S-Gamut3 - S-Log3',
			alias = 'sg3lg3',
			desc = 'Sony S-Gamut3 - S-Log3',
			family = 'Scene-Referred/Sony',
			encoding = 'log',
			chr = 'Sony - S-Gamut3 - Linear',
			tf = tfuncs.get('oetf_sony_slog3'),
		),
		Colorspace(
			name = 'Sony - S-Gamut3.Cine - Linear',
			alias = 'sg3cln',
			desc = 'Sony S-Gamut3.Cine - Linear\nThe Cine variation of S-Gamut3 is more closely aligned to P3 and is more suitable as a grading colorspace.',
			family = 'Scene-Referred/Sony',
			encoding = 'scene-linear',
			chr = [0.766, 0.275, 0.225, 0.8, 0.089, -0.087, 0.3127, 0.329],
		),
		Colorspace(
			name = 'Sony - S-Gamut3.Cine - S-Log3',
			alias = 'sg3clg3',
			desc = 'Sony S-Gamut3.Cine - S-Log3',
			family = 'Scene-Referred/Sony',
			encoding = 'log',
			chr = 'Sony - S-Gamut3.Cine - Linear',
			tf = tfuncs.get('oetf_sony_slog3'),
		),
		Colorspace(
			name = 'Sony - Venice S-Gamut3 - Linear',
			alias = 'vsg3ln',
			desc = 'Sony Venice S-Gamut3 - Linear\nRGBW xy Chromaticity coordinates calculated from the AP0 3x3 matrix available here:\nhttps://github.com/ampas/aces-core/blob/710ecbe52c87ce9f4a1e02c8ddf7ea0d6b611cc8/transforms/ctl/idt/vendorSupplied/sony/IDT.Sony.Venice_SLog3_SGamut3.ctl',
			family = 'Scene-Referred/Sony',
			encoding = 'scene-linear',
			chr = [0.740464264304292, 0.27936437475066, 0.089241145423286, 0.893809528608105, 0.110488236673827, -0.052579333080476, 0.3127, 0.329],
		),
		Colorspace(
			name = 'Sony - Venice S-Gamut3 - S-Log3',
			alias = 'vsg3lg3',
			desc = 'Sony Venice S-Gamut3 - S-Log3',
			family = 'Scene-Referred/Sony',
			encoding = 'log',
			chr = 'Sony - Venice S-Gamut3 - Linear',
			tf = tfuncs.get('oetf_sony_slog3'),
		),
		Colorspace(
			name = 'Sony - Venice S-Gamut3.Cine - Linear',
			alias = 'vsg3cln',
			desc = 'Sony Venice S-Gamut3.Cine - Linear\nRGBW xy Chromaticity coordinates calculated from the AP0 3x3 matrix available here:\nhttps://github.com/ampas/aces-core/blob/710ecbe52c87ce9f4a1e02c8ddf7ea0d6b611cc8/transforms/ctl/idt/vendorSupplied/sony/IDT.Sony.Venice_SLog3_SGamut3Cine.ctl',
			family = 'Scene-Referred/Sony',
			encoding = 'scene-linear',
			chr = [0.775901871567345, 0.274502392854799, 0.188682902773355, 0.828684937020288, 0.101337382499301, -0.089187517306263, 0.3127, 0.329],
		),
		Colorspace(
			name = 'Sony - Venice S-Gamut3.Cine - S-Log3',
			alias = 'vsg3clg3',
			desc = 'Sony Venice S-Gamut3.Cine - S-Log3',
			family = 'Scene-Referred/Sony',
			encoding = 'log',
			chr = 'Sony - Venice S-Gamut3.Cine - Linear',
			tf = tfuncs.get('oetf_sony_slog3'),
		),
	]

	# Display Colorspaces
	display_referred_colorspaces = [
		Colorspace(
			name = 'Rec.709 - Linear',
			alias = 'bt709ln',
			desc = 'ITU-R Recommendation BT.709 Gamut - Linear',
			encoding = 'scene-linear',
			family = 'Display-Referred/Display Gamuts',
			chr = [0.64, 0.33, 0.3, 0.6, 0.15, 0.06, 0.3127, 0.329],
		),
		Colorspace(
			name = 'Rec.2020 - Linear',
			alias = 'bt2020ln',
			desc = 'ITU-R Recommendation BT.2020 Gamut - Linear',
			encoding = 'scene-linear',
			family = 'Display-Referred/Display Gamuts',
			chr = [0.708, 0.292, 0.17, 0.797, 0.131, 0.046, 0.3127, 0.329],
		),
		Colorspace(
			name = 'P3D65 - Linear',
			alias = 'p3d65ln',
			desc = 'P3 Gamut Linear, with a D65 whitepoint.',
			encoding = 'scene-linear',
			family = 'Display-Referred/Display Gamuts',
			chr = [0.68, 0.32, 0.265, 0.69, 0.15, 0.06, 0.3127, 0.329],
		),
		Colorspace(
			name = 'Display Encoding - Rec1886',
			alias = 'bt1886',
			desc = 'Display encoding for an ITU-R Recommendation BT.1886 display with BT.709 primaries and a 2.4 power EOTF',
			family = 'Display-Referred/Display Encoding',
			encoding = 'sdr-video',
			# chr = 'Rec.709 - Linear', # no gamut conversion, just display encoding inverse EOTF
			tf = ocio_xform_exp(2.4, inv=True),
			forward = False,
		),
		Colorspace(
			name = 'Display Encoding - sRGB Display',
			alias = 'srgbg22',
			desc = 'Display encoding - sRGB Display with BT.709 primaries and pure 2.2 Power Electrical-Optical Transfer Function (EOTF)\nAlso called "sRGB Display" as proposed by Filmlight\nhttps://www.youtube.com/watch?v=NzhUzeNUBuM',
			family = 'Display-Referred/Display Encoding',
			encoding = 'sdr-video',
			# chr = 'Rec.709 - Linear',
			tf = ocio_xform_exp(2.2, inv=True),
			forward = False,
		),
		Colorspace(
			name = 'Display Encoding - sRGB Piecewise',
			alias = 'srgb',
			desc = 'Display encoding - sRGB display with BT.709 primaries and ~2.2 power piecewise EOCF (Electrical to Optical Coding Function)\nThe piecewise encoding function from the IEC 61966-2-1 sRGB specification,\nsometimes incorrectly used as a display EOTF.',
			family = 'Display-Referred/Display Encoding',
			encoding = 'sdr-video',
			# chr = 'Rec.709 - Linear',
			tf = tfuncs.get('eocf_srgb'),
			forward = False,
		),
		Colorspace(
			name = 'Display Encoding - DCI P3',
			alias = 'p3d65g26',
			desc = 'Display encoding - DCI display with P3 primaries and pure 2.6 power EOTF',
			family = 'Display-Referred/Display Encoding',
			encoding = 'sdr-video',
			# chr = 'P3D65 - Linear',
			tf = ocio_xform_exp(2.6, inv=True),
			forward = False,
		),
	]

	colorspaces = working_colorspaces + camera_colorspaces + display_referred_colorspaces
	return colorspaces