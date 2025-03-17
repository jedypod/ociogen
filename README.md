# OCIOGen
is a minimal from-scratch OpenColorIO config generator. It has only one dependency: `opencolorio`. 

All gamut conversion matrices are calculated from scratch using [colorimetry math](/utilities/colorimetry.py).

## Install Dependencies
Make sure you have python version 3.7 or greater, then: `python3 -m pip install opencolorio`

## Usage Instructions
Open `ociogen.py` with python. This will launch a very ugly but functional user interface as shown below:
![screenshot_2025-03-16_22-10-21](https://github.com/user-attachments/assets/9150dae2-afb2-428d-9382-48a7dc88fb01)

You can 
- enter the name of your config and the parent directory you want to save it into
- choose whether you want to create an OCIO v1.0 or an OCIO v2.0 config. 1.0 will use `.spi1d` LUTs for the transfer functions, while 2.0 will try to use built in camera log functions where possible.
- select the colorspaces you want added to your config
- choose the reference space (all gamut conversion matrices will be in reference to this colorspace, and all linear roles will be set to this)
- choose the reference log space (all log roles will be set to this, for example `color_timing`)
- click "Generate Config", and edit the result to add your own views.
