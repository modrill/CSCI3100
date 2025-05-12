from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os
import logging
from datetime import datetime
import json
from decimal import Decimal

# 设置更详细的日志格式
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 添加Decimal类型的JSON序列化支持
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
logger.debug(f"Python path: {sys.path}")

try:
    from lib.database.operations import execute_query, execute_update
    from lib.database.exception import DatabaseError
    logger.debug("成功导入数据库操作模块")
except ImportError as e:
    logger.error(f"导入数据库模块失败: {str(e)}")
    sys.exit(1)

app = Flask(__name__)
# 使用自定义的JSON编码器
app.json_encoder = CustomJSONEncoder

# Configure CORS
CORS(app, resources={
    r"/api/admin/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# Simple authentication middleware
def admin_required(f):
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        logger.debug(f"收到认证头: {auth_header}")
        if not auth_header or 'admin' not in auth_header:
            logger.warning(f"认证失败: {auth_header}")
            return jsonify({'error': 'Admin privileges required'}), 403
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/api/admin/items', methods=['GET'])
@admin_required
def get_items():
    """Get all products with pagination"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        offset = (page - 1) * per_page
        
        logger.debug(f"尝试获取产品列表: 页码={page}, 每页数量={per_page}, 偏移量={offset}")
        
        # Query total products count
        count_result = execute_query(
            "SELECT COUNT(*) as total FROM products",
            fetch_one=True
        )
        total = count_result['total']
        logger.debug(f"产品总数: {total}")
        
        # 添加测试代码，查看数据库中前5条记录，帮助调试
        test_products = execute_query(
            "SELECT productID, productName FROM products LIMIT 5",
        )
        logger.debug(f"数据库中的前5条记录: {test_products}")
        
        # Query paginated product list with category and brand names
        products = execute_query(
            """
            SELECT p.productID, p.productName, p.descri, p.price, 
                   p.categoryID, c.categoryName, 
                   p.brandID, b.brandName, 
                   p.img, p.currentStatus, p.inventoryCount, 
                   p.rating, p.sales
            FROM products p
            LEFT JOIN category c ON p.categoryID = c.categoryID
            LEFT JOIN brand b ON p.brandID = b.brandID
            ORDER BY CAST(p.productID AS UNSIGNED)
            LIMIT %s OFFSET %s
            """,
            params=(per_page, offset)
        )
        
        logger.debug(f"查询到 {len(products)} 条产品记录")
        if products:
            logger.debug(f"第一条产品记录: {products[0]}")
        
        # 修改图片路径以兼容两种格式
        for product in products:
            if 'img' in product and product['img']:
                # 确保图片路径正确，添加前缀如果需要
                if not product['img'].startswith('/images/products/'):
                    product['img'] = '/images/products/' + product['img']
                    logger.debug(f"修正图片路径: {product['img']}")
        
        response_data = {
            'products': products,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        }
        
        logger.debug(f"返回响应，总页数: {response_data['total_pages']}")
        return jsonify(response_data), 200
        
    except DatabaseError as e:
        logger.error(f"数据库操作错误: {str(e)}")
        return jsonify({'error': f'Database error: {str(e)}'}), 500
    except Exception as e:
        logger.error(f"获取产品列表时发生错误: {str(e)}", exc_info=True)
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/admin/items/<string:product_id>', methods=['GET'])
@admin_required
def get_item(product_id):
    """Get a single product details"""
    try:
        product = execute_query(
            """
            SELECT p.productID, p.productName, p.descri, p.price, 
                   p.categoryID, c.categoryName, 
                   p.brandID, b.brandName, 
                   p.img, p.currentStatus, p.inventoryCount, 
                   p.rating, p.sales
            FROM products p
            LEFT JOIN category c ON p.categoryID = c.categoryID
            LEFT JOIN brand b ON p.brandID = b.brandID
            WHERE p.productID = %s
            """,
            params=(product_id,),
            fetch_one=True
        )
        
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        # 修改图片路径以兼容两种格式
        if 'img' in product and product['img']:
            # 确保图片路径正确，添加前缀如果需要
            if not product['img'].startswith('/images/products/'):
                product['img'] = '/images/products/' + product['img']
            
        return jsonify(product), 200
        
    except DatabaseError as e:
        logger.error(f"Database operation error: {str(e)}")
        return jsonify({'error': f'Database error: {str(e)}'}), 500
    except Exception as e:
        logger.error(f"Error getting product details: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/admin/categories', methods=['GET'])
@admin_required
def get_categories():
    """Get all categories"""
    try:
        categories = execute_query(
            "SELECT categoryID, categoryName FROM category ORDER BY categoryName"
        )
        
        return jsonify(categories), 200
        
    except DatabaseError as e:
        logger.error(f"Database operation error: {str(e)}")
        return jsonify({'error': f'Database error: {str(e)}'}), 500
    except Exception as e:
        logger.error(f"Error getting categories: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/admin/brands', methods=['GET'])
@admin_required
def get_brands():
    """Get all brands"""
    try:
        brands = execute_query(
            "SELECT brandID, brandName FROM brand ORDER BY brandName"
        )
        
        return jsonify(brands), 200
        
    except DatabaseError as e:
        logger.error(f"Database operation error: {str(e)}")
        return jsonify({'error': f'Database error: {str(e)}'}), 500
    except Exception as e:
        logger.error(f"Error getting brands: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/admin/items', methods=['POST'])
@admin_required
def create_item():
    """Create a new product"""
    try:
        data = request.get_json()
        product_id = data.get('productID')
        product_name = data.get('productName')
        description = data.get('descri', '')
        price = data.get('price')
        category_id = data.get('categoryID')
        brand_id = data.get('brandID')
        img = data.get('img')
        current_status = data.get('currentStatus', 0)
        inventory_count = data.get('inventoryCount', 0)
        rating = data.get('rating', 0.0)
        sales = data.get('sales', 0)
        
        # Validate required fields
        if not all([product_id, product_name, price, img]):
            return jsonify({'error': 'Product ID, name, price and image are required'}), 400
            
        # Check if product ID already exists
        existing_product = execute_query(
            "SELECT productID FROM products WHERE productID = %s",
            params=(product_id,),
            fetch_one=True
        )
        
        if existing_product:
            return jsonify({'error': 'Product ID already exists'}), 400
        
        # Validate price is positive
        try:
            price_value = float(price)
            if price_value < 0.01:
                return jsonify({'error': 'Price must be at least 0.01'}), 400
        except ValueError:
            return jsonify({'error': 'Invalid price value'}), 400
            
        # Create new product
        execute_update(
            """
            INSERT INTO products 
            (productID, productName, descri, price, categoryID, brandID, 
            img, currentStatus, inventoryCount, rating, sales)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            params=(product_id, product_name, description, price, category_id, brand_id, 
                    img, current_status, inventory_count, rating, sales)
        )
        
        return jsonify({'message': 'Product created successfully'}), 201
        
    except DatabaseError as e:
        logger.error(f"Database operation error: {str(e)}")
        return jsonify({'error': f'Database error: {str(e)}'}), 500
    except Exception as e:
        logger.error(f"Error creating product: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/admin/items/<string:product_id>', methods=['PUT'])
@admin_required
def update_item(product_id):
    """Update a product"""
    try:
        data = request.get_json()
        product_name = data.get('productName')
        description = data.get('descri')
        price = data.get('price')
        category_id = data.get('categoryID')
        brand_id = data.get('brandID')
        img = data.get('img')
        current_status = data.get('currentStatus')
        inventory_count = data.get('inventoryCount')
        rating = data.get('rating')
        sales = data.get('sales')
        
        # Check if product exists
        existing_product = execute_query(
            "SELECT productID FROM products WHERE productID = %s",
            params=(product_id,),
            fetch_one=True
        )
        
        if not existing_product:
            return jsonify({'error': 'Product not found'}), 404
            
        # Build update query
        update_fields = []
        params = []
        
        if product_name is not None:
            update_fields.append("productName = %s")
            params.append(product_name)
            
        if description is not None:
            update_fields.append("descri = %s")
            params.append(description)
            
        if price is not None:
            # Validate price is positive
            try:
                price_value = float(price)
                if price_value < 0.01:
                    return jsonify({'error': 'Price must be at least 0.01'}), 400
                update_fields.append("price = %s")
                params.append(price)
            except ValueError:
                return jsonify({'error': 'Invalid price value'}), 400
            
        if category_id is not None:
            update_fields.append("categoryID = %s")
            params.append(category_id)
            
        if brand_id is not None:
            update_fields.append("brandID = %s")
            params.append(brand_id)
            
        if img is not None:
            update_fields.append("img = %s")
            params.append(img)
            
        if current_status is not None:
            update_fields.append("currentStatus = %s")
            params.append(current_status)
            
        if inventory_count is not None:
            # Validate inventory is non-negative
            try:
                count_value = int(inventory_count)
                if count_value < 0:
                    return jsonify({'error': 'Inventory count cannot be negative'}), 400
                update_fields.append("inventoryCount = %s")
                params.append(inventory_count)
            except ValueError:
                return jsonify({'error': 'Invalid inventory value'}), 400
            
        if rating is not None:
            update_fields.append("rating = %s")
            params.append(rating)
            
        if sales is not None:
            update_fields.append("sales = %s")
            params.append(sales)
            
        if not update_fields:
            return jsonify({'message': 'No fields provided for update'}), 400
            
        # Execute update
        params.append(product_id)
        query = f"UPDATE products SET {', '.join(update_fields)} WHERE productID = %s"
        
        result = execute_update(query, params=params)
        
        if result <= 0:
            return jsonify({'error': 'Update failed'}), 500
            
        return jsonify({'message': 'Product updated successfully'}), 200
        
    except DatabaseError as e:
        logger.error(f"Database operation error: {str(e)}")
        return jsonify({'error': f'Database error: {str(e)}'}), 500
    except Exception as e:
        logger.error(f"Error updating product: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/admin/items/<string:product_id>', methods=['DELETE'])
@admin_required
def delete_item(product_id):
    """Delete a product"""
    try:
        # Check if product exists
        existing_product = execute_query(
            "SELECT productID FROM products WHERE productID = %s",
            params=(product_id,),
            fetch_one=True
        )
        
        if not existing_product:
            return jsonify({'error': 'Product not found'}), 404
            
        # Execute delete
        result = execute_update(
            "DELETE FROM products WHERE productID = %s",
            params=(product_id,)
        )
        
        if result <= 0:
            return jsonify({'error': 'Delete failed'}), 500
            
        return jsonify({'message': 'Product deleted successfully'}), 200
        
    except DatabaseError as e:
        logger.error(f"Database operation error: {str(e)}")
        return jsonify({'error': f'Database error: {str(e)}'}), 500
    except Exception as e:
        logger.error(f"Error deleting product: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/admin/search-items', methods=['GET'])
@admin_required
def search_items():
    """Search products by name, ID, or description"""
    try:
        keyword = request.args.get('keyword', '')
        if not keyword:
            return jsonify({'error': 'Please provide a search keyword'}), 400
            
        search_term = f'%{keyword}%'
        products = execute_query(
            """
            SELECT p.productID, p.productName, p.descri, p.price, 
                   p.categoryID, c.categoryName, 
                   p.brandID, b.brandName, 
                   p.img, p.currentStatus, p.inventoryCount, 
                   p.rating, p.sales
            FROM products p
            LEFT JOIN category c ON p.categoryID = c.categoryID
            LEFT JOIN brand b ON p.brandID = b.brandID
            WHERE p.productID LIKE %s OR p.productName LIKE %s OR p.descri LIKE %s
            ORDER BY CAST(p.productID AS UNSIGNED)
            """,
            params=(search_term, search_term, search_term)
        )
        
        # 修改图片路径以兼容两种格式
        for product in products:
            if 'img' in product and product['img']:
                # 确保图片路径正确，添加前缀如果需要
                if not product['img'].startswith('/images/products/'):
                    product['img'] = '/images/products/' + product['img']
        
        return jsonify({'products': products}), 200
        
    except DatabaseError as e:
        logger.error(f"Database operation error: {str(e)}")
        return jsonify({'error': f'Database error: {str(e)}'}), 500
    except Exception as e:
        logger.error(f"Error searching products: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/admin/generate-product-id', methods=['GET'])
@admin_required
def generate_product_id():
    """Generate a unique product ID"""
    try:
        # Get the latest product ID
        latest_product = execute_query(
            "SELECT productID FROM products ORDER BY CAST(productID AS UNSIGNED) DESC LIMIT 1",
            fetch_one=True
        )
        
        if not latest_product:
            # If no products exist, start with P000000000001
            new_id = "P000000000001"
        else:
            # Increment the latest ID
            latest_id = latest_product['productID']
            
            # 处理纯数字ID
            if latest_id.isdigit():
                try:
                    num = int(latest_id)
                    new_num = num + 1
                    new_id = str(new_num)
                except ValueError:
                    # 如果转换失败，使用时间戳
                    import time
                    new_id = str(int(time.time()))
            # 处理以P开头的ID格式
            elif latest_id.startswith('P'):
                num_part = latest_id[1:]
                try:
                    num = int(num_part)
                    new_num = num + 1
                    new_id = f"P{new_num:012d}"
                except ValueError:
                    # 如果转换失败，使用时间戳
                    import time
                    new_id = f"P{int(time.time()):012d}"
            else:
                # 如果ID不符合任何模式，使用时间戳
                import time
                new_id = str(int(time.time()))
                
        return jsonify({'productID': new_id}), 200
        
    except DatabaseError as e:
        logger.error(f"Database operation error: {str(e)}")
        return jsonify({'error': f'Database error: {str(e)}'}), 500
    except Exception as e:
        logger.error(f"Error generating product ID: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/admin/test-db', methods=['GET'])
def test_db():
    """测试数据库连接和基本查询"""
    try:
        # 测试数据库连接
        logger.debug("测试数据库连接...")
        
        # 测试查询 products 表
        products_count = execute_query(
            "SELECT COUNT(*) as count FROM products", 
            fetch_one=True
        )
        logger.debug(f"产品总数: {products_count}")
        
        # 测试查询 category 表
        categories = execute_query("SELECT * FROM category")
        logger.debug(f"类别数: {len(categories)}")
        
        # 测试查询 brand 表
        brands = execute_query("SELECT * FROM brand")
        logger.debug(f"品牌数: {len(brands)}")
        
        # 测试获取前5条产品记录
        products = execute_query(
            "SELECT productID, productName, categoryID, brandID FROM products LIMIT 5"
        )
        
        # 测试连表查询
        joined_products = execute_query(
            """
            SELECT p.productID, p.productName, c.categoryName, b.brandName
            FROM products p
            LEFT JOIN category c ON p.categoryID = c.categoryID
            LEFT JOIN brand b ON p.brandID = b.brandID
            LIMIT 5
            """
        )
        
        return jsonify({
            'status': 'success',
            'products_count': products_count,
            'categories': categories,
            'brands': brands,
            'sample_products': products,
            'joined_products': joined_products
        }), 200
        
    except DatabaseError as e:
        logger.error(f"数据库操作错误: {str(e)}")
        return jsonify({'error': f'Database error: {str(e)}'}), 500
    except Exception as e:
        logger.error(f"测试数据库时发生错误: {str(e)}", exc_info=True)
        return jsonify({'error': f'Server error: {str(e)}'}), 500

if __name__ == '__main__':
    logger.info("启动 admin_items 后端服务，端口 5003...")
    app.run(debug=True, port=5003) 