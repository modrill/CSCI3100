/*
我是注释
购物车的后端 针对购物车的页面（暂时没有其他页面的联动）
目前有四个功能
连接数据库
读取商品
往购物车里添加商品
读取购物车里的东西
*/
<?php
//init db
$host = '1234';
$dbname = 'yythaoye';
$user = 'taotao';
$pass = '123456';

try {
    $pdo = new PDO("mysql:host=$host;dbname=$dbname;charset=utf8", $user, $pass);
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
} catch (PDOException $e) {
    die("connection failed: " . $e->getMessage());
}
function getSessionId() {
    if (!isset($_COOKIE['cart_session'])) {
        $sessionId = bin2hex(random_bytes(16));
        setcookie('cart_session', $sessionId, time() + (86400 * 30), "/");
        return $sessionId;
    }
    return $_COOKIE['cart_session'];
}
?>

<?php
require '../config/db.php';
//商品
try {
    $stmt = $pdo->query("SELECT * FROM products");
    $products = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    header('Content-Type: application/json');
    echo json_encode($products);
} catch (PDOException $e) {
    http_response_code(500);
    echo json_encode(['error' => 'cannot get products']);
    error_log($e->getMessage());
}
?>


<?php
require '../config/db.php';

//往购物车里添加商品

session_start();
$sessionId = getSessionId();

$data = json_decode(file_get_contents('php://input'), true);
$productId = filter_var($data['product_id'], FILTER_VALIDATE_INT);

try {
    // 检查库存
    $stmt = $pdo->prepare("SELECT stock FROM products WHERE product_id = ?");
    $stmt->execute([$productId]);
    $stock = $stmt->fetchColumn();
    
    if ($stock < 1) {
        echo json_encode(['success' => false, 'message' => 'no enough stock']);
        exit;
    }

    // 插入或更新购物车
    $stmt = $pdo->prepare("
        INSERT INTO carts (session_id, product_id, quantity)
        VALUES (:session_id, :product_id, 1)
        ON DUPLICATE KEY UPDATE quantity = quantity + 1
    ");
    
    $stmt->execute([
        ':session_id' => $sessionId,
        ':product_id' => $productId
    ]);

    echo json_encode(['success' => true]);
    
} catch (PDOException $e) {
    http_response_code(500);
    echo json_encode(['success' => false, 'message' => 'database error']);
}
?>

<?php
require '../config/db.php';
//购物车里的东西
$sessionId = getSessionId();

try {
    $stmt = $pdo->prepare("
        SELECT p.product_id, p.name, p.price, c.quantity 
        FROM carts c
        JOIN products p ON c.product_id = p.product_id
        WHERE c.session_id = ?
    ");
    $stmt->execute([$sessionId]);
    $cartItems = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    header('Content-Type: application/json');
    echo json_encode($cartItems);
    
} catch (PDOException $e) {
    http_response_code(500);
    echo json_encode(['error' => 'fail to fetch cart items']);
}
?>