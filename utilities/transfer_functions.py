import math

''' ##################################################################
    # Camera Optical To Electrical Transfer Functions
    ##################################################################
'''

# tfuncs = {}

def oetf_acescc(x, inv=False):
  ''' ACEScc Log
      S-2014-003 : ACEScc - A Quasi-Logarithmic Encoding of ACES Data for use within Color Grading Systems
      http://j.mp/S-2014-003
  '''
  # constants
  A = 9.72
  B = 17.52
  if inv: # log to lin
    return (2**(x*B - A) - 2**-16)*2 if x <= (A - 15)/B else 2**(x*B - A) if x < (math.log2(65504) + A)/B else x
  else: # lin to log
    return (math.log2(2**-16) + A)/B if x <= 0.0 else (math.log2(2**-16 + x/2) + A)/B if x < 2**-15 else (math.log2(x) + A)/B
# tfuncs['oetf_acescc'] = oetf_acescc

def oetf_acescct(x, inv=False):
  ''' ACEScct Log
      S-2016-001 : ACEScct - A Quasi-Logarithmic Encoding of ACES Data for use within Color Grading Systems
      http://j.mp/S-2016-001_
  '''
  # constants
  cut1 = 0.0078125
  cut2 = 0.155251141552511
  A = 10.5402377416545
  B = 0.0729055341958355
  C = 9.72
  D = 17.52
  
  if inv: # log to lin
    return (x-B)/A if x <= cut2 else 2.0**(x*D-C)
  else: # lin to log
    return A*x+B if x <= cut1 else (math.log2(x) + C)/D
# tfuncs['oetf_acescct'] = oetf_acescct

def oetf_filmlight_tlog(x, inv=False):
  ''' Filmlight T-Log
      Specified in the flspace file included with the Baselight software
      /etc/colourspaces/FilmLight_TLog_EGamut.flspace
  '''
  # constants 
  o = 0.075
  A = 0.5520126568606655
  B = 0.09232902596577353
  C = 0.0057048244042473785
  G = 16.184376489665897
  
  if inv: # log to lin
    return (x-o)/G if x < o else math.exp((x - A)/B) - C
  else: # lin to log
    return G*x + o if x < 0.0 else math.log(x + C)*B + A
# tfuncs['oetf_filmlight_tlog'] = oetf_filmlight_tlog
  
def oetf_davinci_intermediate(x, inv=False):
  ''' DaVinci Intermediate Log
      https://documents.blackmagicdesign.com/InformationNotes/DaVinci_Resolve_17_Wide_Gamut_Intermediate.pdf
  '''
  # Constants
  A = 0.0075
  B = 7.0
  C = 0.07329248
  M = 10.44426855
  LIN_CUT = 0.00262409
  LOG_CUT = 0.02740668
  
  if inv: # log to lin
    return x/M if x <= LOG_CUT else math.pow(2.0, (x/C) - B) - A
  else: # lin to log
    return x*M if x <= LIN_CUT else (math.log2(x + A) + B)*C
# tfuncs['oetf_davinci_intermediate'] = oetf_davinci_intermediate

def oetf_arri_logc3(x, inv=False):
  ''' Arri LogC3 EI800
      https://www.arri.com/resource/blob/31918/66f56e6abb6e5b6553929edf9aa7483e/2017-03-alexa-logc-curve-in-vfx-data.pdf
  '''
  cut, a, b, c, d, e, f = (0.010591, 5.555556, 0.052272, 0.247190, 0.385537, 5.367655, 0.092809)
  
  if inv: # log to lin
    return (math.pow(10.0, (x - d)/c) - b)/a if x > e*cut + f else (x - f)/e
  else: # lin to log
    return c*math.log10(a*x + b) + d if x > cut else e*x + f
# tfuncs['oetf_arri_logc3'] = oetf_arri_logc3

def oetf_arri_logc4(x, inv=False):
  ''' Arri LogC4
      https://www.arri.com/resource/blob/278790/bea879ac0d041a925bed27a096ab3ec2/2022-05-arri-logc4-specification-data.pdf
  '''
  # constants
  a = (2.0**18.0 - 16.0)/117.45
  b = (1023.0 - 95.0)/1023.0
  c = 95.0/1023.0
  s = (7.0*math.log(2.0)*2.0**(7.0 - 14.0*c/b))/(a*b)
  t = (2.0**(14.0*(-c/b) + 6.0) - 64.0)/a

  if inv: # log to lin
    return x*s + t if x < t else (2.0**(14.0*(x - c)/b + 6.0) - 64.0)/a
  else: # lin to log
    return (x - t)/s if x < t else (math.log2(a*x + 64.0) - 6.0)/14.0*b + c
# tfuncs['oetf_arri_logc4'] = oetf_arri_logc4

def oetf_blackmagic_bmdfilmgen5(x, inv=False):
  ''' Blackmagic Film Generation 5
      Specified in the Blackmagic Generation 5 Color Science whitepaper included in the Blackmagic Raw SDK available here
      https://www.blackmagicdesign.com/support/download/1bad3dc74c2c4a908ce5c9ce8b9f74f8/Linux
      At this path in the installer:
      /usr/lib64/blackmagic/BlackmagicRAWSDK/Documents/Blackmagic Generation 5 Color Science Technical Reference.pdf
  '''
  # Constants
  A = 0.08692876065491224
  B = 0.005494072432257808
  C = 0.5300133392291939
  D = 8.283605932402494
  E = 0.09246575342465753
  LIN_CUT = 0.005
  LOG_CUT = D * LIN_CUT + E
  
  if inv: # log to lin
    return (x - E)/D if x < LOG_CUT else math.exp((x - C)/A) - B
  else: # lin to log
    return D*x + E if x < LIN_CUT else A*math.log(x + B) + C
# tfuncs['oetf_blackmagic_bmdfilmgen5'] = oetf_blackmagic_bmdfilmgen5

def oetf_canon_clog2(x, inv=False):
  ''' Canon CLog2
      CLog2 is intended for grading workflows, whereas CLog3 is intended for a more "direct to display" workflow.
      
      Canon log transfer functions are all described in this whitepaper:
      https://downloads.canon.com/nw/learn/white-papers/cinema-eos/white-paper-canon-log-gamma-curves.pdf

      The log transfer functions described above match the 1D LUTs available in the "Canon lookup table Version 201911" 
      download available here
      https://www.usa.canon.com/internet/portal/us/home/support/details/cameras/cinema-eos/cinema-eos-c500-mark-ii?tab=drivers_downloads

      However in the CTL ACES IDT provided in the "Input Transform Version 202007 for EOS C500 Mark II" file 
      at the above url, they add the /=0.9 on the scene-linear values. This function matches the IDT.
  '''
  # constants
  c0 = 0.092864125
  c1 = 0.24136077
  c2 = 87.099375
  
  if inv: # log to lin
    x = -(math.pow(10.0, (c0 - x)/c1) - 1.0)/c2 if x < c0 else (math.pow(10.0, (x - c0)/c1) - 1.0)/c2
    return x*0.9
  else: # lin to log
    x /= 0.9
    return -c1*math.log10(1.0 - c2*x) + c0 if x < 0.0 else c1*math.log10(c2*x + 1.0) + c0
# tfuncs['oetf_canon_clog2'] = oetf_canon_clog2

def oetf_canon_clog3(x, inv=False):
  ''' Canon CLog3
      Same source as CLog2 above
  '''
  # constants
  sp0 = 0.014
  sp1 = 0.09746547
  sp2 = 0.15277891
  c0 = 0.36726845
  c1 = 14.98325
  c2 = 0.12783901
  c3 = 1.9754798
  c4 = 0.12512219
  c5 = 0.12240537
    
  if inv: # log to lin
    x = -(math.pow(10.0, (c2 - x)/c0) - 1.0)/c1 if x < sp1 else (x - c4)/c3 if x <= sp2 else (math.pow(10.0, (x - c5)/c0) - 1.0)/c1
    return x*0.9
  else: # lin to log
    x = x/0.9
    return -c0*math.log10(1.0 - c1*x) + c2 if x < -sp0 else c3*x + c4 if x <= sp0 else c0*math.log10(c1*x + 1.0) + c5
# tfuncs['oetf_canon_clog3'] = oetf_canon_clog3

def oetf_kodak_cineon(x, inv=False):
  ''' Kodak Cineon Log
      https://github.com/imageworks/OpenColorIO-Configs/blob/master/nuke-default/make.py
  '''
  a = 685.0
  b = 300.0
  c = 95.0
  
  off = math.pow(10.0, (c - a)/b)
  
  if inv: # log to lin
    return ((math.pow(10.0, ((1023.0*x - a)/b)) - off)/(1.0 - off))
  else: # lin to log
    return ((a + b*math.log10(x*(1.0 - off) + off))/1023.0)
# tfuncs['oetf_kodak_cineon'] = oetf_kodak_cineon

def oetf_dji_dlog(x, inv=False):
  ''' DJI D-Log
      https://dl.djicdn.com/downloads/zenmuse+x7/20171010/D-Log_D-Gamut_Whitepaper.pdf
  '''
  if inv: # log to lin
    return (x - 0.0929)/6.025 if x <= 0.14 else (math.pow(10.0, (3.89616*x - 2.27752)) - 0.0108)/0.9892
  else: # lin to log
    return 6.025*x + 0.0929 if x <= 0.0078 else (math.log10(x*0.9892 + 0.0108))*0.256663 + 0.584555
# tfuncs['oetf_dji_dlog'] = oetf_dji_dlog

def oetf_fujifilm_flog(x, inv=False):
  ''' Fujifilm F-Log
      https://dl.fujifilm-x.com/support/lut/F-Log_DataSheet_E_Ver.1.0.pdf
  '''
  # constants
  a = 0.555556
  b = 0.009468
  c = 0.344676
  d = 0.790453
  e = 8.735631
  f = 0.092864
  cut1 = 0.00089
  cut2 = 0.1005377752

  if inv: # log to lin
    return (x-f)/e if x < cut2 else (math.pow(10.0, ((x - d)/c))/a - b/a)
  else: # lin to log
    return e*x+f if x < cut1 else c*math.log10(a*x + b) + d
# tfuncs['oetf_fujifilm_flog'] = oetf_fujifilm_flog

def oetf_fujifilm_flog2(x, inv=False):
  ''' Fujifilm F-Log2
      https://dl.fujifilm-x.com/support/lut/F-Log2_DataSheet_E_Ver.1.0.pdf
  '''
  # constants
  a = 5.555556
  b = 0.064829
  c = 0.245281
  d = 0.384316
  e = 8.799461
  f = 0.092864
  cut1 = 0.000889
  cut2 = 0.100686685370811

  if inv: # log to lin
    return (x-f)/e if x < cut2 else (math.pow(10.0, ((x - d)/c))/a - b/a)
  else: # lin to log
    return e*x+f if x < cut1 else c*math.log10(a*x + b) + d
# tfuncs['oetf_fujifilm_flog2'] = oetf_fujifilm_flog2

def oetf_gopro_protune(x, inv=False):
  ''' GoPro Protune Flat log curve
      Unable to find whitepaper on this but it is described in this file from the original HPD opencolorio ACES config:
      https://github.com/hpd/OpenColorIO-Configs/blob/master/aces_1.0.3/python/aces_ocio/colorspaces/gopro.py
  '''
  
  if inv: # log to lin
    return (math.pow(113.0, x) - 1.0)/112.0 if x > 0.0 else 0.0
  else: # lin to log
    return math.log(x*112.0 + 1.0)/math.log(113.0) if x > 0.0 else 0.0
# tfuncs['oetf_gopro_protune'] = oetf_gopro_protune

def oetf_leica_llog(x, inv=False):
  ''' Leica L-Log
      https://leica-camera.com/sites/default/files/pm-65977-210914__L-Log_Reference_Manual_EN.pdf
  '''
  # constants
  a = 8.0
  b = 0.09
  c = 0.27
  d = 1.3
  e = 0.0115
  f = 0.6
  c0 = 0.006
  c1 = 0.138
  
  if inv: # log to lin
    return (x - b)/a if x < c1 else (math.pow(10.0, (x - f)/c) - e)/d
  else: # lin to log
    return a*x + b if x < c0 else c*math.log10(d*x + e) + f
# tfuncs['oetf_leica_llog'] = oetf_leica_llog

def oetf_nikon_nlog(x, inv=False):
  ''' Nikon N-Log
      http://download.nikonimglib.com/archive3/hDCmK00m9JDI03RPruD74xpoU905/N-Log_Specification_(En)01.pdf
  '''
  # constants
  a = 619.0/1023.0
  b = 150.0/1023.0
  c = 650.0/1023.0
  d = 0.0075
  c0 = 452.0/1023.0
  c1 = 0.328
  
  if inv: # log to lin
    return math.exp((x - a)/b) if x > c0 else math.pow(x/c, 3.0) - d if x > 0.0 else 0.0
  else: # lin to log
    return b*math.log(x) + a if x > c1 else c*math.pow(x + d, 1.0/3.0) if x > 0.0 else 0.0
# tfuncs['oetf_nikon_nlog'] = oetf_nikon_nlog

def oetf_panasonic_vlog(x, inv=False):
  ''' Panasonic V-Log
      https://pro-av.panasonic.net/en/cinema_camera_varicam_eva/support/pdf/VARICAM_V-Log_V-Gamut.pdf
  '''
  # constants
  cut1 = 0.01
  cut2 = 0.181
  b = 0.00873
  c = 0.241514
  d = 0.598206
  
  if inv: # log to lin
    return (x - 0.125)/5.6 if x < cut2 else math.pow(10.0, (x - d)/c) - b
  else: # lin to log
    return 5.6*x + 0.125 if x < cut1 else c*math.log10(x + b) + d
# tfuncs['oetf_panasonic_vlog'] = oetf_panasonic_vlog

def oetf_red_log3g10(x, inv=False):
  ''' Red Log3G10
      https://docs.red.com/955-0187/PDF/915-0187%20Rev-C%20%20%20RED%20OPS,%20White%20Paper%20on%20REDWideGamutRGB%20and%20Log3G10.pdf
  '''
  # constants
  a = 0.224282
  b = 155.975327
  c = 0.01
  g = 15.1927

  if inv: # log to lin
    return (x/g) - c if x < 0.0 else (math.pow(10.0, x/a) - 1.0)/b - c
  else: # lin to log
    return (x + c)*g if x < -c else a*math.log10((x + c)*b + 1.0)
# tfuncs['oetf_red_log3g10'] = oetf_red_log3g10

def oetf_sony_slog2(x, inv=False):
  ''' Sony S-Log2
      from the pdf originally retrieved from :
      https://pro.sony/ue_US/?sonyref=pro.sony.com/bbsccms/assets/files/micro/dmpc/training/S-Log2_Technical_PaperV1_0.pdf
      Link is down, here is a mirror:
      https://mega.nz/file/e6hDxC5b#YaRzePfGFFPkx_hRtmqw2gTT0NIPuzlJycwCP38H720
  '''
  # constants
  c0 = 0.432699
  c1 = 155.0
  c2 = 219.0
  c3 = 0.037584
  c4 = 0.616596
  c5 = 0.03
  c6 = 3.53881278538813
  c7 = 0.030001222851889303
  
  if inv: # log to lin
    x = (x - 64.0/1023.0)/(876.0/1023.0)
    x = (x - c7)/c6 if x < c7 else c2*(math.pow(10.0, ((x - c4 - c5)/c0)) - c3)/c1
    return x*0.9
  else: # lin to log
    x = x/0.9
    x = x*c6 + c7 if x < 0.0 else (c0*math.log10(c1*x/c2 + c3) + c4) + c5
    return x*(876.0/1023)+64/1023
# tfuncs['oetf_sony_slog2'] = oetf_sony_slog2

def oetf_sony_slog3(x, inv=False):
  ''' Sony S-Log3
      https://pro.sony/s3/cms-static-content/uploadfile/06/1237494271406.pdf
  '''
  # constants
  a = 0.01125
  b = 420.0
  c = 261.5
  d = 171.2102946929
  e = 95.0
  f = 0.18
  o = 0.01
  
  if inv: # log to lin
    return (x*1023.0 - e)*a/(d-e) if x < d/1023.0 else (math.pow(10.0, ((x*1023.0 - b)/c))*(f + o) - o)
  else: # lin to log
    return (x*(d - e)/a + e)/1023.0 if x < a else (b + math.log10((x + o)/(f + o))*c)/1023.0
# tfuncs['oetf_sony_slog3'] = oetf_sony_slog3

def oetf_apple_log(x, inv=False):
  ''' Apple Log
      Official links to whitepaper and LUTs (behind an Apple Developer paywall D: )
      https://download.developer.apple.com/Developer_Tools/Apple_Log_profile/Apple_Log_Profile_White_Paper.pdf
      https://download.developer.apple.com/Developer_Tools/Apple_Log_profile/AppleLogLUTsv1.zip
      
      Someone posted them both on this forum thread though:
      https://discussions.apple.com/thread/255147293?page=2
      https://netorg5834184-my.sharepoint.com/:f:/g/personal/scot_infilmsdesign_com/EmKSceiQwv1FoXrPFqmQCAIB0iIDSq_ARks4BrkN5uRJAw?e=VLjSdE
  '''
  # constants
  R_0 = -0.05641088
  R_t = 0.01
  c = 47.28711236
  b = 0.00964052
  g = 0.08550479
  d = 0.69336945
  P_t = c*(R_t - R_0)**2

  if inv:
    return math.pow(2, (x - d)/g) - b if x >= P_t else math.sqrt(x/c) + R_0 if x >= 0 else R_0
  else:
    return g*math.log2(x+b)+d if x >= R_t else c*(x-R_0)**2 if x >= R_0 else 0
# tfuncs['oetf_apple_log'] = oetf_apple_log

def oetf_jplog2(x, inv=False):
  ''' JPLog2
      This is the log curve that Josh Pines contributed to the ACESLog Virtual Working Group:
      https://community.acescentral.com/t/aceslog-strawman-proposal/5270

      And then further popularized / promoted as proprietary technology by Dado Valentic:
      https://colourlab.ai/jplog2	
  '''
  ln_s = 10.36773919972907075549
  ln_o = 0.09077750069969257965
  if inv:
    return (x - ln_o)/ln_s if x <= 0.16129032258064516129 else math.pow(2, x*20.46 - 10.5)
  else:
    return ln_s*x + ln_o if x <= 0.006801176276 else (math.log2(x) + 10.5)/20.46
# tfuncs['oetf_jplog2'] = oetf_jplog2




''' ##################################################################
    # Electrical To Optical Encoding Functions (EOTFs)
    ##################################################################
'''

def eotf_power(x, p, inv=False):
  # wrapper function for power
  if x <= 0.0:
    return 0.0
  else:
    return x**(1.0/p) if inv else x**p

def eotf_srgb(x, inv=False):
  ''' The sRGB Electrical-Optical Transfer Function (EOTF)
      Also called "sRGB Display" as proposed by Filmlight
      https://www.youtube.com/watch?v=NzhUzeNUBuM
  '''
  return eotf_power(x, 2.2, inv=inv)


def eotf_rec1886(x, inv=False):
  ''' Pure 2.4 Power EOTF for use in a Rec.1886 Display
      ITU-R Reccomendation BT.1886 EOTF
      https://www.itu.int/dms_pubrec/itu-r/rec/bt/R-REC-BT.1886-0-201103-I!!PDF-E.pdf
  '''
  return eotf_power(x, 2.4, inv=inv)


def eotf_gamma26(x, inv=False):
  ''' 2.6 Power EOTF for use in a DCI theater projection
      Pure 2.6 power EOTF often used in theatrical digital cinema
  '''
  return eotf_power(x, 2.6, inv=inv)


def eotf_st2084(x, inv=False):
  ''' ST2084 PQ EOTF
      This function does not normalize: 1.0 is 10,000 nits.

      For a 600 nit peak luminance, one would normalize x to
      x *= 600/10000
      
      ITU-R Rec BT.2100-2 https://www.itu.int/rec/R-REC-BT.2100
      ITU-R Rep BT.2390-9 https://www.itu.int/pub/R-REP-BT.2390
  '''
  if x <= 0.0:
    return 0.0
  # constants
  Lp = 1.0 # We normalize for HDR peak display luminance elsewhere
  m1 = 2610.0 / 16384.0
  m2 = 2523.0 / 32.0
  c1 = 107.0 / 128.0
  c2 = 2413.0 / 128.0
  c3 = 2392.0 / 128.0
  
  x = max(x, 0.0)
  if inv:
    x = (x/Lp)**m1
    return ((c1 + c2*x)/(1.0 + c3*x))**m2
  else:
    x = x**(1.0/m2)
    return ((x - c1)/(c2 - c3*x))**(1.0/m1)*Lp
# tfuncs['eotf_st2084'] = eotf_st2084


def eotf_hlg(rgb, inv=False):
  ''' HLG EOTF
      Aply the HLG Forward or Inverse EOTF. Implements the full ambient surround illumination model
      ITU-R Reccomendation BT.2100-2 https://www.itu.int/rec/R-REC-BT.2100
      ITU-R Reccomendation BT.2390-8: https://www.itu.int/pub/R-REP-BT.2390
      Perceptual Quantiser (PQ) to Hybrid Log-Gamma (HLG) Transcoding: 
      https://www.bbc.co.uk/rd/sites/50335ff370b5c262af000004/assets/592eea8006d63e5e5200f90d/BBC_HDRTV_PQ_HLG_Transcode_v2.pdf
  '''
  HLG_Lw = 1000.0
  HLG_Lb = 0.0
  HLG_Ls = 5.0
  h_a = 0.17883277
  h_b = 1.0 - 4.0*0.17883277
  h_c = 0.5 - h_a*math.log(4.0*h_a)
  h_g = 1.2*(1.111**math.log2(HLG_Lw/1000.0))*(0.98**math.log2(max(1e-6, HLG_Ls)/5.0))
  if inv:
    Yd = 0.2627*rgb[0] + 0.6780*rgb[1] + 0.0593*rgb[2]
    for c in range(3):
      # HLG Inverse OOTF
      rgb[c] = rgb[c]*(Yd**(1.0 - h_g) / h_g)
      # HLG OETF
      rgb[c] = math.sqrt(3.0*rgb[c]) if rgb[c] <= 1.0/12.0 else h_a*math.log(12.0*rgb[c] - h_b) + h_c
  else:
    for c in range(3):
      # HLG Inverse OETF
      rgb[c] = rgb[c]*rgb[c]/3.0 if rgb[c] <= 0.5 else (math.exp((rgb[c] - h_c)/h_a) + h_b) / 12.0
      # HLG OOTF
      Ys = 0.2627*rgb[0] + 0.6780*rgb[1] + 0.0593*rgb[2]
      rgb = rgb*(Ys**(h_g - 1.0))
  return rgb
# tfuncs['eotf_hlg'] = eotf_hlg


def eocf_srgb(x, inv=False):
  ''' sRGB Electro-Optical Coding Function (EOCF)
      The piecewise encoding function from the IEC 61966-2-1 sRGB specification,
      sometimes incorrectly used as a monitor EOTF for an sRGB Display. 
      The correct EOTF for an sRGB Display is a 2.2 power function.
      https://www.desmos.com/calculator/wqh4zdnksz
      https://webstore.iec.ch/publication/6169
  '''
  # constants
  c = 0.04045
  p = 2.4
  o = 0.055
  m = 12.92

  if inv:
    return x/m if x <= c else ((x + o)/(1.0 + o))**p
  else:
    return x*m if x <= c/m else (1.0 + o)*x**(1.0/p) - o
# tfuncs['eocf_srgb'] = eocf_srgb


def eocf_rec709(x, inv=False):
  ''' The Rec.709 Camera Optical to Electrical Coding Function (OETF)
      From ITU-R Recommendation BT.709: https://www.itu.int/rec/R-REC-BT.709
      
      Note: The Rec.709 OETF is sometimes incorrectly used as a replacement 
      for a  display EOTF. When used in this fashion it functions as a kind of 
      primitive view transform by increasing contrast and adding some flare
      compensation in the shadows. However it does not have any compression 
      of highlight values above 1.0, and is therefore really unsuiteable 
      for use in a modern color pipeline. We define it here for this purpose
      as an "Electrical to Optical Coding Function" (EOCF).
  '''
  if inv:
    return x/4.5 if x < 0.081 else ((x + 0.099)/1.099)**(1/0.45)
  else:
    return 4.5*x if x < 0.018 else 1.099*x**0.45 - 0.099
# tfuncs['eocf_rec709'] = eocf_rec709


