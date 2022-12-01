 # generate_bill

使用softlayer API 产生一段时期范围内的所有账单信息
## 安装依赖性包
pip3 install SoftLayer

## 使用
- 根据日期范围列出所有发票  
./generate_bill.py -s 03/01/2022 -e 03/30/2022 -f pdf -k <api-key> -u <username> -t ALL  
- 根据日期范围和发票类型过滤发票  
```
# 提取时间范围从 03/01/2022 到 03/30/2022之间，账单类型为CREDIT 和  ONE-TIME-CHARGE 类型的账单，并保存为PDF
./generate_bill.py -s 03/01/2022 -e 03/30/2022 -f pdf -k <api-key> -u <username> -t CREDIT -t ONE-TIME-CHARGE
```

## 参数
- `-s` 起始日志 格式为 03/30/2022  月/日/年
- `-s` 截止日志 格式为 03/30/2022  月/日/年
- `-f` 输出格式， 支持pdf和 xls
- `-k` Softlayer API key
- `-u` Softlayer username
- `-t` 发票类型，SoftLayer发票和服务信用根据其类型进行区分， 支持下列发票类型。
    - "ALL" 列出所有发票类型
    - "NEW" 类型代码表示新服务的发票。SoftLayer客户的第一张发票具有NEW类型代码。
    - "RECURRING" 发票是在SoftLayer客户每月服务的周年结算日生成的。
    - "ONE-TIME-CHARGE" 发票产生时，一次性收费应用到一个帐户。
    - "CREDIT" 每当SoftLayer对账户余额应用贷方时，就会生成发票。
    - "REFUND" 类型信贷是针对客户的帐户余额及其应收账款的应用。
    - "MANUAL_PAYMENT_CREDIT" 每当客户进行计划外付款时,就会生成发票积分。


# generate_bill_summary

使用softlayer API 产生一段时期范围内的所有账单摘要信息
## 安装依赖性包
pip3 install SoftLayer

## 设置环境变量
```
echo SL_USERNAME=<replace-it> > env.sh
echo SL_API_KEY==<replace-it> >> env.sh
source env.sh
```

## 使用
- 根据日期范围列出所有发票摘要并保存到本地excel文档
./generate_bill_summary.py -s 03/01/2022 -e 03/30/2022 -k <api-key> -u <username> -t ALL
- 根据日期范围和发票类型过滤发票

```
# 提取时间范围从 03/01/2022 到 03/30/2022之间，账单类型为CREDIT 和  ONE-TIME-CHARGE 类型的账单摘要信息，并保存本地excel文档  
./generate_bill_summary.py -s 03/01/2022 -e 03/30/2022  -k <api-key> -u <username> -t CREDIT -t ONE-TIME-CHARGE  
```

## 参数
- `-s` 起始日志 格式为 03/30/2022  月/日/年
- `-s` 截止日志 格式为 03/30/2022  月/日/年
- `-k` Softlayer API key
- `-u` Softlayer username
- `-t` 发票类型，SoftLayer发票和服务信用根据其类型进行区分， 支持下列发票类型。
    - "ALL" 列出所有发票类型
    - "NEW" 类型代码表示新服务的发票。SoftLayer客户的第一张发票具有NEW类型代码。
    - "RECURRING" 发票是在SoftLayer客户每月服务的周年结算日生成的。
    - "ONE-TIME-CHARGE" 发票产生时，一次性收费应用到一个帐户。
    - "CREDIT" 每当SoftLayer对账户余额应用贷方时，就会生成发票。
    - "REFUND" 类型信贷是针对客户的帐户余额及其应收账款的应用。
    - "MANUAL_PAYMENT_CREDIT" 每当客户进行计划外付款时,就会生成发票积分。

# 获取月初预付费 类型为`RECURRING`的账单
./month_invoice.py -s 12/01/2021 -e 12/31/2021 -t RECURRING > bill.json 

# month_invoice 获取整月费用
合并多个账单到一个月账单
一个月中的账单通常由一下三部分组成
 - 每个月1日预收取到按月付费机器的类型为`RECURRING`的账单
 - 月中新下设备的类型为`NEW`的账单
 - 从备件库里提取设备或升级设备产生的类型为`ONE-TIME-CHARGE`的账单
由于一个月的实践费用为以上类型的多个账单组成，可以使用下面脚本获取整个月的费用，这个脚本最好在当月中没有新费用产生的时候运行。  
比如12月15日跑的脚本产生的费用为整个12月的预付费加上14日之前的账单，如果16日从备件库里新提取设备，脚本需要重新跑  
注意： 目前脚本只能处理从备件库提取的设备产生的ONE-TIME-CHARGE账单，对于升级设备还没有处理，会作为单独项目列出。
```sh
 ./month_invoice.py -s 12/01/2021 -e 12/31/2021   -t RECURRING -t NEW -t ONE-TIME-CHARGE > bill.json   
 ```