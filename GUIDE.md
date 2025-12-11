# 混合数据库架构使用指南

## 架构概述

本项目采用 **MySQL + MongoDB** 混合数据库架构：

- **MySQL (关系型数据库)**: 存储核心业务数据
  - 用户信息、商店信息、图书基础信息
  - 订单数据、库存数据
  - 支持ACID事务，保证数据一致性

- **MongoDB (NoSQL数据库)**: 存储BLOB数据  
  - 图书详细描述、作者介绍、目录内容
  - 图书封面图片等二进制数据
  - 系统日志数据

## 环境配置

### 1. MySQL 安装和配置

**Ubuntu/Linux:**
```bash
# 安装MySQL
sudo apt update
sudo apt install mysql-server

# 启动MySQL服务
sudo systemctl start mysql
sudo systemctl enable mysql

# 安全配置
sudo mysql_secure_installation

# 登录MySQL并创建用户
sudo mysql
CREATE USER 'bookstore'@'localhost' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON bookstore.* TO 'bookstore'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

**Windows:**
1. 下载MySQL安装包: https://dev.mysql.com/downloads/installer/
2. 安装并设置root密码为'password'
3. 启动MySQL服务

### 2. MongoDB 安装和配置

**Ubuntu/Linux:**
```bash
# 导入MongoDB公钥
wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add -

# 添加MongoDB源
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list

# 安装MongoDB
sudo apt-get update
sudo apt-get install -y mongodb-org

# 启动MongoDB服务
sudo systemctl start mongod
sudo systemctl enable mongod
```

### 3. Python依赖安装

```bash
# 安装Python依赖
pip install -r requirements.txt
```

### 4. 环境变量配置 (可选)

创建 `.env` 文件：
```bash
# MySQL配置
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=bookstore
MYSQL_USER=root
MYSQL_PASSWORD=password

# MongoDB配置  
MONGO_HOST=localhost
MONGO_PORT=27017
```

## 数据库初始化

### 1. 初始化数据库结构
```bash
python3 init_database.py
```

### 2. 数据迁移（如果有现有MongoDB数据）
```bash
python3 migrate_to_mysql.py
```

### 3. 从SQLite迁移图书数据（首次使用）
```bash
python3 migrate_sqlite_to_mongo.py  # 先迁移到MongoDB
python3 migrate_to_mysql.py         # 再迁移到混合架构
```

## 运行测试

```bash
# 安装依赖
pip install -r requirements.txt

# 运行测试
bash script/test.sh
```

## 数据库结构说明

### MySQL表结构

1. **users** - 用户信息
2. **stores** - 商店信息  
3. **books** - 图书基础信息
4. **store_inventory** - 商店库存
5. **orders** - 订单信息
6. **order_details** - 订单详情

### MongoDB集合结构

1. **book_details** - 图书详细信息和图片
2. **system_logs** - 系统日志

## 性能优化

1. **索引优化**: MySQL和MongoDB都创建了适当的索引
2. **连接池**: MySQL使用连接池提高性能
3. **数据分离**: 将大文本和二进制数据分离到MongoDB
4. **全文搜索**: 支持MySQL全文索引和MongoDB文本索引

## 故障排除

### 常见问题

1. **MySQL连接失败**
   ```
   mysql.connector.errors.ProgrammingError: 1045 (28000): Access denied
   ```
   - 检查用户名密码是否正确
   - 确认用户有相应权限

2. **MongoDB连接超时**
   ```
   pymongo.errors.ServerSelectionTimeoutError
   ```
   - 检查MongoDB服务是否启动
   - 确认端口27017没有被占用

3. **外键约束错误**
   ```
   mysql.connector.errors.IntegrityError: 1452 (23000): Cannot add or update a child row
   ```
   - 确保引用的父记录存在
   - 检查数据迁移顺序

## 监控和维护

1. **性能监控**: 使用MySQL Performance Schema和MongoDB Profiler
2. **备份策略**: 定期备份MySQL和MongoDB数据
3. **日志分析**: 查看系统日志集合分析系统状态

## 开发建议

1. **事务管理**: 对于需要一致性的操作，使用MySQL事务
2. **查询优化**: 合理使用索引，避免全表扫描
3. **缓存策略**: 对热点数据考虑使用Redis缓存
4. **分页查询**: 大量数据查询时使用分页