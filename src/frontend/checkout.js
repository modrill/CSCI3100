async function checkout() {
    const userId = document.getElementById('userId').value.trim();
    const shippingAddress = document.getElementById('shippingAddress').value.trim();
    const paymentMethod = document.getElementById('paymentMethod').value;

    if (!userId || !shippingAddress) {
        alert("请填写用户ID和收货地址！");
        return;
    }

    const payload = {
        UserID: userId,
        ShippingAddress: shippingAddress,
        PaymentMethod: paymentMethod
    };

    try {
        // 修改成你的后端实际访问地址
        const response = await fetch("/checkout", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });
        const result = await response.json();

        if (response.ok) {
            document.getElementById("resultLog").textContent =
                "请求成功，返回结果:\n" + JSON.stringify(result, null, 2);
        } else {
            document.getElementById("resultLog").textContent =
                "请求失败，返回结果:\n" + JSON.stringify(result, null, 2);
        }
    } catch (err) {
        document.getElementById("resultLog").textContent =
            "网络或服务器错误：" + err.message;
    }
}
        