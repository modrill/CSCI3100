# CSCI3100

v1.0.0 

src里面存放了front-end/back-end
dataset&database相关可以放在database文件夹里，包括前端素材也可以放进去（或者开个temp文件夹）
某部分的代码可以开个temp文件放着慢慢调试

前端可以先写个框架（黑白框框加文字），后面统一样式再细改
目前我这边用的是php/html+js

米娜桑加油捏(ง •_•)ง

v1.1.0

我在database文件夹里放了一个包含商品分类，品牌和具体描述外加图片的测试数据库
图片路径是images/products/$px$.jpeg，$px$对应的是productId，例如productId为33的商品对应的图片是p33.jpeg
继承使用apache+mysql+php，算法部分我准备用python编写
大家还有需要的信息我可以再加进去，比如其他的商品类别和商品信息

期末周加油捏(｀･ω･´)ゞ

v1.1.1

*改进了一下buyzu_item.sql，字段名和schema.sql里面的保持一致了，然后下面是暂定的变量定义：*
**已废除**

v1.1.2

数据库字段名用了更规范的驼峰命名法，详情参见database/buyzu_item.sql里面的具体定义

v1.1.3
   lib/database - >database 包，提供数据库操作函数。使用说明在database方法说明.txt

v1.1.4
    cart与checkout 连接。
    目前情况：checkout的跳转？0
    -》cart连接数据库读取。（现在用的临时函数）

v1.1.5

更新了数据库，上传了更多用于测试的图片和记录

v1.1.6
目前要做的：
1.需不需要admin？要什么功能？
2.测试：连接/操作数据库
3. 后端需要修改一下url调用，目前无法转页面