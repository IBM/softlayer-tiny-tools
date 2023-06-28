

#### set env
#!/bin/bash
export ACCESS_KEY=<replace-access-key>
export API_ENDPOINT=<replace-endpoint>
export TAGS=<your-tag-with-format-"setup:test,os:centos6,project:roe,location:us,role:ops">

### install 
yum update
yum install psmisc
./install.sh