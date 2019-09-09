# Boru - Lab Automated Deployment System
*files*
- **boru(.py)** - Main scheduler
- **webAPI(.py)** - REST and Bottle
- **requestHandler(.py)** - API validation
- **adminHandler(.py)** - */adminScripts* validation
- **DBConnect(.py)** - Communication from */scripts* to MongoDB

*folders*
- **/scripts** - Scripts called by the scheduler
- **/plugins** - Plugins called by the scripts
- **/notificationPlugins** - Notifications called by the scheduler
- **/adminScripts** - Scripts by the *adminHandler(.py)*
- **/views** - Bottle .tpl files
- **/usefulScripts** - Other scripts