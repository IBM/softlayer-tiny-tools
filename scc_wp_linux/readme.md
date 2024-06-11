

#### set env
```sh
export ACCESS_KEY=<replace-access-key>
export API_ENDPOINT=<region>.security-compliance-secure.cloud.ibm.com
export TAGS=<your-tag-with-format-"setup:test,os:centos6,project:roe,location:us,role:ops">
```

### install 
```sh
yum update -y
yum install -y git psmisc
git clone https://github.com/IBM/softlayer-tiny-tools.git
cd softlayer-tiny-tools/scc_wp_linux/
./install.sh
```