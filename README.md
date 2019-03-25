# AUTO CATCH IGG GIFT CODE DAILY

## requirement
    1. python3 enviroment
    2. python3-pip
    3. python3 packages:
        3.1 cv2
        3.2 numpy
        3.3 lxml
        3.4 urllib
        3.5 eic_utils
        3.6 sqlite

## what you need do
1. set up file 'config.json'. write {"igg\_id": "YOUR IGG ID"} in config.json, like:
    echo '{"igg_id": "123123123"}' > config.json
2. run 
    python3 igg.py

## what else you need do
after some requests (usually 50 times), there will be captcha in the cmdline, input the captcha you see, then can continue :)   
usually you should expand the window to the max to see the captcha,   
or you need to fix captcha's size in igg.py line #92: change 170, 170 to any size smaller.

