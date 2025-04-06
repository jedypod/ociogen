# Whitepaper Sources

## ACES
- ACEScc
  `ACES_ACEScc__S-2014-003.pdf`
  S-2014-003 : ACEScc - A Quasi-Logarithmic Encoding of ACES Data for use within color Grading Systems 
  http://j.mp/S-2014-003
- ACEScct 
  `ACES_ACEScct__S-2016-001.pdf`
  S-2016-001 : ACEScct - A Quasi-Logarithmic Encoding of ACES Data for use within Color Grading Systems 
  http://j.mp/S-2016-001_
- JPLog2
  This is the log curve that Josh Pines contributed to the now-defunct ACESLog Virtual Working Group:
  https://community.acescentral.com/t/aceslog-strawman-proposal/5270

  And then further popularized / promoted as proprietary technology by Dado Valentic:
  https://colourlab.ai/jplog2	

## Arri
- Arri LogC3 EI800
	https://www.arri.com/resource/blob/31918/66f56e6abb6e5b6553929edf9aa7483e/2017-03-alexa-logc-curve-in-vfx-data.pdf
	
- Arri LogC4
  https://www.arri.com/resource/blob/278790/bea879ac0d041a925bed27a096ab3ec2/2022-05-arri-logc4-specification-data.pdf


## Blackmagic
- DaVinci Intermediate Log
  `DaVinci_Resolve_17_Wide_Gamut_Intermediate.pdf`
  https://documents.blackmagicdesign.com/InformationNotes/DaVinci_Resolve_17_Wide_Gamut_Intermediate.pdf

- Blackmagic Film Generation 5
  Specified in the Blackmagic Generation 5 Color Science whitepaper included in the Blackmagic Raw SDK available here
	https://www.blackmagicdesign.com/support/download/1bad3dc74c2c4a908ce5c9ce8b9f74f8/Linux
	At this path in the installer:
	/usr/lib64/blackmagic/BlackmagicRAWSDK/Documents/Blackmagic Generation 5 Color Science Technical Reference.pdf

## Canon
- Canon CLog2 / CLog3
  CLog2 is intended for grading workflows, whereas CLog3 is intended for a more "direct to display" workflow.
  
  Canon log transfer functions are all described in this whitepaper:
  https://downloads.canon.com/nw/learn/white-papers/cinema-eos/white-paper-canon-log-gamma-curves.pdf

  The log transfer functions described above match the 1D LUTs available in the "Canon lookup table Version 201911" 
  download available here
  https://www.usa.canon.com/internet/portal/us/home/support/details/cameras/cinema-eos/cinema-eos-c500-mark-ii?tab=drivers_downloads

  However in the CTL ACES IDT provided in the "Input Transform Version 202007 for EOS C500 Mark II" file 
  at the above url, they add the /=0.9 on the scene-linear values. This function matches the IDT.

## Cineon
- Kodak Cineon Log
  https://github.com/imageworks/OpenColorIO-Configs/blob/master/nuke-default/make.py

## DJI
- DJI D-Log
	https://dl.djicdn.com/downloads/zenmuse+x7/20171010/D-Log_D-Gamut_Whitepaper.pdf

## Filmlight
- TLog
  `FilmLight_TLog_EGamut2.flspace`
  Specified in the flspace file included with the Baselight software
  `/etc/colourspaces/FilmLight_TLog_EGamut.flspace`

## Fujifilm
- Fujifilm F-Log
	https://dl.fujifilm-x.com/support/lut/F-Log_DataSheet_E_Ver.1.0.pdf
- Fujifilm F-Log2
  https://dl.fujifilm-x.com/support/lut/F-Log2_DataSheet_E_Ver.1.0.pdf
  https://fujifilm-x.com/global/support/download/lut/

## GoPro
- GoPro Protune Flat log curve
  Unable to find whitepaper on this but it is described in this file from the original HPD opencolorio ACES config:
  https://github.com/hpd/OpenColorIO-Configs/blob/master/aces_1.0.3/python/aces_ocio/colorspaces/gopro.py

## Leica
- Leica L-Log
	https://leica-camera.com/sites/default/files/pm-118912-L-Log_Reference_Manual_V1.6.pdf

## Nikon
- Nikon N-Log
  http://download.nikonimglib.com/archive3/hDCmK00m9JDI03RPruD74xpoU905/N-Log_Specification_(En)01.pdf

## Panasonic
- Panasonic V-Log
  https://pro-av.panasonic.net/en/cinema_camera_varicam_eva/support/pdf/VARICAM_V-Log_V-Gamut.pdf

## RED
- Red Log3G10
  https://docs.red.com/955-0187/PDF/915-0187%20Rev-C%20%20%20RED%20OPS,%20White%20Paper%20on%20REDWideGamutRGB%20and%20Log3G10.pdf

## Sony
- Sony S-Log2
  from the pdf originally retrieved from :
  https://pro.sony/ue_US/?sonyref=pro.sony.com/bbsccms/assets/files/micro/dmpc/training/S-Log2_Technical_PaperV1_0.pdf
- Sony S-Log3
  https://pro.sony/s3/cms-static-content/uploadfile/06/1237494271406.pdf

## Apple
- Apple Log
  Official links to whitepaper and LUTs (behind an Apple Developer paywall D: )
  https://download.developer.apple.com/Developer_Tools/Apple_Log_profile/Apple_Log_Profile_White_Paper.pdf
  https://download.developer.apple.com/Developer_Tools/Apple_Log_profile/AppleLogLUTsv1.zip
  
  Someone posted them both on this forum thread though:
  https://discussions.apple.com/thread/255147293?page=2
  https://netorg5834184-my.sharepoint.com/:f:/g/personal/scot_infilmsdesign_com/EmKSceiQwv1FoXrPFqmQCAIB0iIDSq_ARks4BrkN5uRJAw?e=VLjSdE

## Samsung
- Samsung Log
  Whitepaper available here (behind registration wall) https://developer.samsung.com/mobile/samsung-log-video.html

## Xiaomi
- Xiaomi Log
			Whitepaper available here: https://www.mi.com/global/product/aces/

## Rec.2100 ST2084-PQ
- ST2084 PQ EOTF
  ITU-R Rec BT.2100-2 https://www.itu.int/rec/R-REC-BT.2100
  ITU-R Rep BT.2390-9 https://www.itu.int/pub/R-REP-BT.2390

## Rec.2100 HLG
- HLG EOTF
  ITU-R Reccomendation BT.2100-2 https://www.itu.int/rec/R-REC-BT.2100
  ITU-R Reccomendation BT.2390-8: https://www.itu.int/pub/R-REP-BT.2390
  Perceptual Quantiser (PQ) to Hybrid Log-Gamma (HLG) Transcoding: 
  https://www.bbc.co.uk/rd/sites/50335ff370b5c262af000004/assets/592eea8006d63e5e5200f90d/BBC_HDRTV_PQ_HLG_Transcode_v2.pdf

## sRGB
- https://webstore.iec.ch/en/publication/6169
- sRGB Display
  The sRGB Electrical-Optical Transfer Function (EOTF)
  Also called "sRGB Display" as proposed by Filmlight
  https://www.youtube.com/watch?v=NzhUzeNUBuM
- sRGB Encoding
  The piecewise encoding function from the IEC 61966-2-1 sRGB specification,
  sometimes incorrectly used as a monitor EOTF for an sRGB Display. 
  The correct EOTF for an sRGB Display is a 2.2 power function.
  https://webstore.iec.ch/publication/6169

## Rec.1886
- https://www.itu.int/rec/R-REC-BT.1886-0-201103-I

