# <img src='https://0000.us/klatchat/app/files/neon_images/icons/neon_skill.png' card_color="#FF8600" width="50" style="vertical-align:bottom">Device Control Center

## Summary

Handles system-wide settings and controls.

## Requirements

No special required packages for this skill.

## Description

Device Control skill handles base core/OS controls and interactions It is responsible for:

-   Changing dialog modes;
    
-   Clearing recorded likes, audio, selected and full text transcriptions, and the rest of the user’s data;
    
-   Audible commands to switch between skipping and requiring wake words in two modes: dev and user;

-   Shutting down the whole device;
    
-   Exiting from Neon’s process;

  

## Examples

First, make your request. Say `“Hey Neon”` if you are in the wake words mode. Then say your desired command. Use the following list as a reference:

- "Change your dialog mode to (random/default)"
- "clear my user (profile/transcripts/likes/media/preferences/languages)"
- "skip wake words"
- "require wake words"
- "I want you to exit"
- "I want you to shutdown"
- "I want you to restart"

## Additional Documentation
### Change dialog mode

I want you to begin {dialogmode} (dialog|dialogue) mode  
Change your (dialog|dialogue) mode to {dialogmode}

  

Where *dialog mode* is one of the following:

-   random
    
-   default
    
-   primary
    
-   normal
    

### Clear variety of recorded data

    I want to clear my user *data option*
    
    neon clear my user *data option*
    
    erase all of my user *data option*

  

where *data option* is one of the following:

-   data
    
-   transcripts
    
-   selected transcriptions
    
-   like
    
-   brands
    
-   ignored brands
    
-   pictures and videos
    
-   media
    
-   preferences
    
-   languages
    
-   cached responses
    
-   profile
    

### Switch between skipping and requiring wake words

If you are in devMode, your commands are limited to the following in order to avoid false-positives:

    -   require {ww}
        
    -   quit skipping {ww}
    

  

and

  

    -   skip {ww}
        
    -   begin skipping {ww}
        

  

where *{ww}* stands for wake words.

If you are in user mode, you can use the following commands to use wakewords:

    -   solo mode
        
    -   I am in (a group |group)
        
    -   I am not alone
        
    -   use {ww}
        
    -   require {ww}
        
    -   begin requiring {ww}
        
    -   stop (skipping {ww} |solo mode )
        
    -   end (skipping {ww} |solo mode )
        
    -   deny (skipping {ww} |solo mode )
        
    -   quit (skipping {ww} |solo mode )
    

  

And the following to start skipping the wakewords:

    -   I am alone
        
    -   skip {ww}
        
    -   start ( skipping {ww} | solo mode )
        
    -   begin ( skipping {ww} | solo mode )
        
    -   allow ( skipping {ww} | solo mode )
        
    -   enter ( skipping {ww} | solo mode )

Most likely, Neon will ask for the confirmation to most of the choices available above. Follow the prompts and reply 
either with simple positive or negative answer, or follow it up by the requested 3-digit code.

Wait for the successful confirmation or action execution from Neon. Most commands should be instantaneous.

## Details

### Text

        Neon, begin skipping wake words
        >> Should I start skipping wake words?
        Yes
        >> Okay, Starting to skip wake words.
    
        Require wake words.
        >> Should I start requiring wake words?
        Yes
        >> Okay, entering wake words mode.

Please refer to [How to Use](how-to-use) for more information.

### Picture

### Video

## Contact Support

Use the [link](https://neongecko.com/ContactUs) or [submit an issue on GitHub](https://help.github.com/en/articles/creating-an-issue)

## Credits
[NeonGeckoCom](https://github.com/NeonGeckoCom)
[reginaneon](https://github.com/reginaneon)
[NeonDaniel](https://github.com/NeonDaniel)

## Category
**Configuration**
Daily

## Tags
#NeonGecko Original
#NeonAI
#controls
#device
#wake words
#power
#settings




