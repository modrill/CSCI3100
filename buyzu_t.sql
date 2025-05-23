-- 重建 buyzu 数据库
DROP DATABASE IF EXISTS buyzu;
CREATE DATABASE IF NOT EXISTS buyzu;
USE buyzu;

-- 验证码表
CREATE TABLE IF NOT EXISTS verification_codes (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    email       VARCHAR(255) NOT NULL,
    code        VARCHAR(10)  NOT NULL,
    expiry_time DATETIME      NOT NULL,
    INDEX idx_verif_email (email)
) ENGINE=InnoDB CHARSET=utf8mb4;

-- 用户表（已含管理员标识与创建时间）
CREATE TABLE IF NOT EXISTS users (
    id          BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    username    VARCHAR(50)  NOT NULL UNIQUE,
    password    VARCHAR(255) NOT NULL,
    email       VARCHAR(255) NOT NULL UNIQUE,
    google_id   VARCHAR(255) DEFAULT NULL UNIQUE,
    is_admin    TINYINT(1)   NOT NULL DEFAULT 0,
    createdAt   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_email (email)
) ENGINE=InnoDB CHARSET=utf8mb4;

-- 如需初始化一个默认 Admin 账号（密码为 'ABCdef123' 的 Hash，实际请替换）
INSERT INTO users (username, password, email, is_admin)
VALUES (
  'admin',
  'scrypt:32768:8:1$Net1dK74p4YuGiUK$d7b88f7e6e26a4936b1a0e7d0b67b44860dc6dbd4c21f9e3d2362339df7b3c3d2ec95726bb10b494ac87d5df980585539124adb2a26e63cfa8a5e951152a0ac8',
  'admin@example.com',
  1
)
ON DUPLICATE KEY UPDATE is_admin=1;

INSERT INTO users (username, password, email, is_admin)
VALUES (
  'asdf',
  'scrypt:32768:8:1$Net1dK74p4YuGiUK$d7b88f7e6e26a4936b1a0e7d0b67b44860dc6dbd4c21f9e3d2362339df7b3c3d2ec95726bb10b494ac87d5df980585539124adb2a26e63cfa8a5e951152a0ac8',
  'modrill@example.com',
  0
)
ON DUPLICATE KEY UPDATE is_admin=1;

-- 创建普通用户并授权
CREATE USER IF NOT EXISTS 'taotao'@'localhost' IDENTIFIED BY '123456';
GRANT ALL PRIVILEGES ON buyzu.* TO 'taotao'@'localhost';
FLUSH PRIVILEGES;

-- Create category table
DROP TABLE IF EXISTS category;
CREATE TABLE IF NOT EXISTS category (
    categoryID INT PRIMARY KEY,
    categoryName VARCHAR(50) NOT NULL
);

-- Insert category data
INSERT INTO category (categoryID, categoryName) VALUES
(1, 'Headphones'),
(2, 'Laptops'),
(3, 'Smartphones'),
(4, 'Smart Watches');
(5, 'Smart TVs');

-- Create brand table
DROP TABLE IF EXISTS brand;
CREATE TABLE IF NOT EXISTS brand (
    brandID   INT           PRIMARY KEY,
    brandName VARCHAR(50)   NOT NULL
) ENGINE=InnoDB CHARSET=utf8mb4;

-- Insert brand data
INSERT INTO brand (brandID, brandName) VALUES
(1, 'Apple'),
(2, 'Sony'),
(3, 'Bose'),
(4, 'Sennheiser'),
(5, 'Beats'),
(6, 'JBL'),
(7, 'Huawei'),
(8, 'Xiaomi'),
(9, 'Bang & Olufsen'),
(10, 'Edifier'),
(11, 'Audio-Technica'),
(12, 'AKG'),
(13, 'Beyerdynamic'),
(14, 'Shure'),
(15, 'Razer'),
(16, 'Logitech'),
(17, 'Shokz'),
(18, 'QCY'),
(19, 'Lenovo'),
(20, 'HP'),
(21, 'ASUS'),
(22, 'Dell'),
(23, 'Acer'),
(24, 'Samsung'),
(25, 'Microsoft'),
(26, 'Gigabyte'),
(27, 'MSI');

-- Create product table
DROP TABLE IF EXISTS products;
CREATE TABLE IF NOT EXISTS products (
    productID         CHAR(12)     PRIMARY KEY,
    productName       VARCHAR(100) NOT NULL,
    descri            TEXT,
    price             DECIMAL(10,2) NOT NULL CHECK(Price >= 0.01),
    categoryID        INT,
    brandID           INT,
    img               VARCHAR(255) NOT NULL,
    currentStatus     TINYINT      NOT NULL DEFAULT 0,
    inventoryCount    INT          NOT NULL DEFAULT 0 CHECK(InventoryCount >= 0),
    rating              FLOAT        NOT NULL,
    sales             INT          NOT NULL,
    CONSTRAINT fk_prod_cat
        FOREIGN KEY (categoryID) REFERENCES category(categoryID)
        ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT fk_prod_brand
        FOREIGN KEY (brandID) REFERENCES brand(brandID)
        ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB CHARSET=utf8mb4;

-- Insert product data
INSERT INTO products (
    productID, productName, categoryID, brandID,
    descri, price, img, currentStatus,
    inventoryCount, rating, sales
) VALUES
(1, 'Apple AirPods Pro (2nd Generation)', 1, 1, 'Pro-level Active Noise Cancellation with 2x more effectiveness, Adaptive Audio blending ANC/Transparency modes, and Personalized Spatial Audio with dynamic head tracking. Features the H2 chip for immersive sound, clinical-grade Hearing Aid capabilities, and IP54 dust/sweat resistance. Offers up to 6 hours of playback (30h with case) and a MagSafe Charging Case with Find My integration.', 1899, 'p1.jpeg', 1, 2436, 4.9, 23130),
(2, 'Apple AirPods (4th Generation)', 1, 1, 'Redesigned for all-day comfort with Adaptive EQ and Personalized Spatial Audio. Powered by the H2 chip for improved call clarity (Voice Isolation) and seamless Apple ecosystem integration. Offers up to 5 hours of playback (30h with case), IP54 resistance, and a 10% smaller USB-C charging case. Available with/without Active Noise Cancellation.', 1399, 'p2.jpeg', 1, 2452, 4.92, 17153),
(3, 'Apple AirPods Max', 1, 1, 'Premium over-ear headphones with custom-built drivers for ultra-low distortion. Features Personalized Spatial Audio with dynamic head tracking, Pro-level ANC, and Transparency mode. Includes a stainless steel frame with breathable knit mesh canopy, up to 20-hour battery life, and seamless device switching via Apple H1 chips.', 3999, 'p3.jpeg', 1, 31, 4.955, 613),
(4, 'QCY AilyPods', 1, 18, 'Budget-friendly TWS earbuds with 25-hour playback, low-latency gaming mode, and one-step pairing. Ideal for casual users seeking reliable sound and portability.', 109.9, 'p4.jpeg', 1, 4934, 4.75, 2711),
(5, 'QCY C30S', 1, 18, 'Open-ear design with C-shaped secure fit, Bluetooth 5.4, and 10.8mm dual-magnet drivers. Features 25-hour total playback, IPX4 water resistance, and AI-enhanced 4-mic ENC calls. Includes a customizable EQ via QCY App and dual-device connectivity.', 199, 'p5.jpeg', 1, 884, 4.95, 880),
(6, 'Sony WF-1000XM5', 1, 2, 'Industry-leading ANC with Dual Processor chips, LDAC Hi-Res audio, and Adaptive Sound Control. IPX4 sweat resistance, 8-hour battery (24h with case), and redesigned ergonomic fit for all-day comfort. Key Tech: 360 Reality Audio, DSEE Extreme upscaling, Speak-to-Chat.”', 1599, 'p6.jpeg', 1, 373, 4.75, 2985),
(7, 'Sony WH-1000XM5', 1, 2, 'Over-ear ANC titan - Auto-optimizing noise cancellation with 8 mics, 30-hour endurance, and Hi-Res Wireless via LDAC. Premium comfort with ultra-soft protein leather earcups. Flagship Feature: Precise Voice Pickup for crystal-clear calls.', 2299, 'p7.jpeg', 1, 350, 4.905, 4019),
(8, 'Sony LinkBuds S', 1, 2, 'World''s smallest ANC earbuds (4.8g). Seamless Ambient/ANC switching, IPX4 waterproofing, and 6-hour playtime. OpenAudio design for situational awareness during workouts. Innovation: Integrated Processor V1 for low-distortion sound.', 699, 'p8.jpeg', 1, 798, 4.7, 2788),
(9, 'Bose QC Ultra Headphones', 1, 3, 'Cinematic Immersive Audio with head tracking, CustomTune adaptive ANC, and 24-hour battery. Luxe leather earcups and multipoint Bluetooth for seamless device switching.', 2799, 'p9.jpeg', 1, 99, 4.3, 1381),
(10, 'Bose Ultra Open Earbuds', 1, 3, 'Open-ear freedom meets Bose OpenAudio tech - directional sound stays private. 7-hour playtime, IPX4 resistance, and cuff-like design for all-day wear without ear fatigue.', 1799, 'p10.jpeg', 1, 293, 4.3, 2635),
(11, 'Sennheiser IE 900', 1, 4, 'Audiophile-grade in-ear monitors with X3R transducer system. Handcrafted in Germany for zero distortion, ultra-wide frequency response (5Hz-48kHz), and detachable OFC cables.', 9999, 'p11.jpeg', 1, 2, 4.75, 119),
(12, 'Sennheiser IE 600', 1, 4, 'Reference-class sound with ZR01 amorphous zirconium drivers. Rugged 3D-printed housings, IPX4 splash-proof, and ultra-low impedance (18Ω) for studio monitoring.', 4599, 'p12.jpeg', 1, 10, 4.75, 225),
(13, 'Sennheiser IE 200', 1, 4, 'Balanced armature drivers meet dynamic bass. Ergonomic fit with TrueResponse tech, detachable MMCX cables, and silicone/foam tips for noise isolation.', 999, 'p13.jpeg', 1, 289, 4.75, 1442),
(14, 'Sennheiser IE 100 PRO', 1, 4, 'Stage-ready wireless monitors - 10mm dynamic drivers, aptX Low Latency, and 10-hour battery. Detachable cables with secure-fit ear hooks for live performances.', 549, 'p14.jpeg', 1, 688, 4.935, 1889),
(15, 'Beats Studio Buds+', 1, 5, '1.6x stronger ANC, 36-hour total playtime, and spatial audio with dynamic head tracking. IPX4 sweat resistance, 3x larger mics for calls, and cross-platform compatibility (iOS/Android).', 899, 'p15.jpeg', 1, 463, 4.2, 2083),
(16, 'Beats Flex', 1, 5, 'Magnetic wireless earbuds with 12-hour playback, Apple W1 chip for seamless iOS pairing, and Fast Fuel charging (10min=1.5hrs). Features Auto-Play/Pause via magnetic tips and Class 1 Bluetooth for stable connections.', 319, 'p16.jpeg', 1, 10158, 4.4, 16202),
(17, 'Beats Solo Buds', 1, 5, 'Ultra-compact true wireless earbuds with 18-hour battery, dual-layer drivers for low distortion, and the smallest charging case ever. Includes four ear tip sizes for secure fit and passive noise isolation.', 699, 'p17.jpeg', 1, 802, 4.3, 2804),
(18, 'JBL T770NC', 1, 6, 'When your music is on, nothing else matters. The JBL Tune 770NC Adaptive Noise Cancelling wireless headphones deliver on that promise all day—and longer, while sparing you the unwanted noises. With up to 70 hours of battery life, you''ll easily get through a busy week of using them and still have enough JBL Pure Bass Sound to get you through the weekend. And if you do need a quick recharge, 5 minutes gets you an extra 3 hours of music. Lightweight, and flat-folding, the JBL Tune 770NC can also connect with two Bluetooth® devices simultaneously, so you''ll never miss a call while watching a movie on your tablet. With the free JBL Headphones app, you can tailor the sound to suit your taste. And voice prompts in your language will guide you through the features. Manage your calls and your voice assistant hassle-free right from your phone and use VoiceAware to hear yourself when you''re speaking. Just choose the color that best suits your vibe, and start having fun.', 449, 'p18.jpeg', 1, 680, 4.85, 1527),
(19, 'JBL SOUNDGEAR SENSE', 1, 6, 'JBL Soundgear Sense true wireless open-ear headphones feature JBL OpenSound Technology with air conduction, which doesn''t completely close off your ear canal, making them comfortable enough to wear for hours. Flexible earhooks rotate, so you can choose whether you want to focus on your music or calls, or let in more sound from the world around you. A detachable neckband provides an even more secure fit while you''re working out, and an IP54 rating means that they can stand up to sweat—or even a light rainfall. Your voice will be crystal clear, even on a windy day, thanks to four voice mics. Customize how you use the intuitive touch controls on each earbud to handle your music and calls with the My JBL Headphones app. JBL Soundgear Sense is as adaptable as you are.', 799, 'p19.jpeg', 1, 1099, 4.95, 4392),
(20, 'JBL WAVE BEAM 2', 1, 6, 'Quality sound just got easier—and more fun. JBL Wave Beam 2 earbuds feature exciting JBL Pure Bass Sound, plus Active Noise Cancelling and Smart Ambient technology so you decide how much of the outside world you want to hear. Manage hands-free crisp, clear calls with just a tap on the earbuds. Use the JBL Headphones app to customize your sound and Voice Prompts language. Connect seamlessly with up to 8 Bluetooth® devices and switch effortlessly from one to another. And with up to 40 hours* of playback time, they''re a great everyday sound companion. (*with ANC off)', 399, 'p20.jpeg', 1, 714, 4.65, 1425),
(21, 'HUAWEI FreeClip', 1, 7, 'Open-ear C-bridge design with 5.6g weight and adaptive L/R switching. Features 10.8mm dual-magnet drivers, spatial audio, and 36-hour total playback. IP54 waterproof for workouts.', 1199, 'p21.jpeg', 1, 2084, 4.96, 12496),
(22, 'HUAWEI FreeLace Pro 2', 1, 7, 'Neckband-style ANC earphones with USB-C direct charging (5min=5hrs), 25-hour battery, and CustomTune adaptive EQ. Includes four silicone ear tips and IP55 waterproofing.', 399, 'p22.jpeg', 1, 622, 4.85, 1240),
(23, 'HUAWEI FreeBuds 6i', 1, 7, '27dB average ANC depth with Smart Dynamic Noise Cancellation 3.0. Equips 11mm quad-magnet drivers for 14Hz bass and 35-hour playback. Supports multi-device connectivity and customizable touch controls.', 449, 'p23.jpeg', 1, 2855, 4.85, 6410),
(24, 'Xiaomi REDMIBuds 6 Pro', 1, 8, 'Redmi Buds 6 Pro deliver Hi-Res sound via custom triple drivers (titanium + piezoelectric) and LDAC support. Industry-leading 55dB ANC adapts 16,000x/sec, while spatial audio tracks head movements. Battery lasts 36hrs (9.5h standalone) with 5-min quick charge. Features dual-device pairing, IP54 resistance, and matte excimer coating. Personalize with app-based EQ/ANC controls.', 339, 'p24.jpeg', 1, 1805, 4.85, 3060),
(25, 'Xiaomi REDMIBuds 7S', 1, 8, 'Redmi Buds 7S: Dual drivers (12.4mm titanium + 5.5mm ceramic) deliver Hi-Res sound with NetEase Cloud Music™ tuning. Semi-in-ear ANC + 9m/s windproof calls. 32hrs battery, spatial audio, and HyperOS multi-device control. IP54 splash-resistant with luxe textured design.', 169, 'p25.jpeg', 1, 1717, 4.85, 1451),
(26, 'Bang & Olufsen Beoplay H100', 1, 9, 'Beoplay H100 delivers Hi-Res Spatial Audio with Dolby Atmos support, advanced spatial processing, and dynamic head tracking for a natural, immersive soundstage. Experience multichannel fidelity, lifelike instrument placement, and reduced listening fatigue. Compatible with stereo and spatial audio formats, it blends free-flowing dynamics with precision—perfect for music, films, and calls. Lightweight yet powerful, with premium materials and seamless connectivity.', 13480, 'p26.jpeg', 1, 1, 4.85, 65),
(27, 'Bang & Olufsen Beoplay H95', 1, 9, 'Beoplay H95 - Flagship over-ear headphones with 40mm titanium drivers for Hi-Res Audio (10-40,000Hz) and 5-level Adaptive ANC. Enjoy up to 50-hour playback (38h with ANC), Bluetooth 5.1 (aptX™ Adaptive/AAC), and ultra-premium materials like lambskin leather and machined aluminum. Features intuitive touch controls, a luxury travel case, and Bang & Olufsen''s signature sound tuning for unmatched clarity and depth.', 5898, 'p27.jpeg', 1, 29, 4.7, 845),
(28, 'Bang & Olufsen Beoplay HX', 1, 9, 'Beoplay HX - Premium wireless headphones with 40mm neodymium drivers for rich, detailed sound. Features Adaptive ANC with True Transparency™, 35-hour battery life (ANC on), and Bluetooth 5.1 (aptX™ Adaptive/AAC). Designed for all-day comfort with lambskin ear cushions, memory foam, and an ultra-light aluminum frame. Includes intuitive controls, multi-device pairing, and IP53 sweat resistance—perfect for work, travel, or immersive listening.', 3398, 'p28.jpeg', 1, 108, 4.8, 1840),
(29, 'Edifier W860NB Pro', 1, 10, 'Audio-Technica ATH-M50xWH: The iconic studio reference headphones, now in sleek white. 45mm drivers with rare-earth magnets deliver pro-level clarity, while swiveling earcups and detachable cables (3 included) ensure versatility. Built for critical listening, DJing, and all-day comfort with upgraded ear pads. Trusted by audio engineers worldwide.', 699, 'p29.jpeg', 1, 1197, 4.8, 4185),
(30, 'Edifier STAX SPIRIT S5', 1, 10, 'Wireless planar magnetic headphones with 2nd-gen EqualMass™ wiring for zero harmonic distortion. Features Snapdragon Sound Suite, 80-hour battery life, and Hi-Res certifications. Includes dual-mic ENC, customizable EQ via EDIFIER ConneX app, and lambskin/cooling-mesh earpads.', 2680, 'p30.jpeg', 1, 66, 4.9, 885),
(31, 'Audio-Technica ATH-M50X WH', 1, 11, 'Edifier W860NB Pro: 40mm titanium-plated drivers with LDAC codec deliver Hi-Res wireless audio. 45dB hybrid ANC (28% improvement) + 4-mic ENC for crystal calls. 55hr battery (ANC on), 10-min quick charge, and multi-point Bluetooth 5.x. Includes app-based EQ/ANC tuning and universal OS support.', 1099, 'p31.jpeg', 1, 3548, 4.9, 19494),
(32, 'Audio-Technica M50XBT2 LAB', 1, 11, 'Limited-edition wireless variant of the ATH-M50x studio headphones, featuring AK4331 DAC, LDAC/AAC codecs, and 50-hour battery. Includes multipoint pairing, low-latency mode, and Google Fast Pair. Designed via fan-voted "LAB M50x" initiative.', 1499, 'p32.jpeg', 1, 118, 4.9, 886),
(33, 'AKG N5005', 1, 12, 'Meticulously crafted from premium gloss black ceramic, the AKG N5005 is the epitome of pure and detailed studio sound reproduction, without distortion or distraction. By pioneering the combination of one dynamic and quad balanced armature drivers in each earphone, AKG gives you perfectly balanced 5-driver configuration headphones and one-of-a-kind sound tuning capabilities that lets you adjust for four precise output preferences. Hi-Res certified, the AKG N5005 replicates the accurate mids, crystal clear highs and warm bass that allows you to be inspired by the purity of music. It perfectly complements your on-the-go lifestyle with its Bluetooth® 4.1 detachable cable, 8-hour (max) battery life, 3-button universal/remote for hands-free, crystal clear calls and a premium carrying case for easy portability.', 3999, 'p33.jpeg', 1, 23, 4.9, 463),
(34, 'AKG N5', 1, 12, 'AKG N5 Hybrid TWS earbuds combine studio-quality sound with intuitive touch controls to deliver an immersive listening experience that fuels your creative focus and fits perfectly in your everyday carry. They connect seamlessly with any device via Bluetooth® or a 2.4GHz USB-C dongle that fits elegantly in the stylish charging case when not in use. The 6 mics deliver perfect call quality in any condition, whether you''re talking one-on-one or in a conference app. Plus, the AKG N5 Hybrid are Zoom-certified. You control the best-in-class True Adaptive Noise Cancelling technology in real time, letting in as much or as little of the outside world as you want via the AKG Headphones app, and controlling how much of your own voice you want to hear during a call. Hi-Res Audio Wireless and immersive spatial audio mean that your music will sound more lifelike than ever. The ergonomic oval shape and custom-size tips let you enjoy heightened clarity and undistorted pure sound all day, every day. And with 10 hours of playtime*, you''ll get through an entire workday before you need to recharge.', 2099, 'p34.jpeg', 1, 41, 4.95, 427),
(35, 'Beyerdynamic Xelento wireless', 1, 13, 'XELENTO wireless is a unique piece of jewellery that embodies the finest audiophile standards and unique craftsmanship - handmade in Heilbronn, Germany. Thanks to the miniaturised Tesla technology, you will discover your music in all its radiance. Experience the full richness of facets with incomparable precision and depth. Indulge yourself in a first-class sound experience wherever you are.', 8399, 'p35.jpeg', 1, 10, 4.8, 422),
(36, 'Beyerdynamic Xelento remote', 1, 13, 'XELENTO remote is a unique piece of audible jewellery that makes audiophiles'' hearts beat faster. Manufactured directly at the company''s headquarters in Heilbronn, this masterpiece of acoustics is created using unique craftsmanship. Driven by beyerdynamic''s Tesla technology in its smallest design yet, the TESLA.11 driver lets music unfold in its full radiance.', 5899, 'p36.jpeg', 1, 15, 4.8, 445),
(37, 'Beyerdynamic T1 III', 1, 13, 'The T1 boast unrivalled richness of detail and spatiality. But we know there''s nothing that can''t be improved, so our acoustical engineers have managed to make our benchmark-setting headphones even better: At the heart of the third-generation T1 is a gently intensified bass to give the very neutral, spatial sound signature even more warmth.', 5899, 'p37.jpeg', 1, 8, 4.85, 227),
(38, 'Beyerdynamic MMX 300 PRO', 1, 13, 'The STELLAR.45 driver, also used in our studio headphones, allows you to hear even the smallest sounds while you''re playing. Thanks to the closed design and unique wearing comfort, you can fully focus on your gameplay and communicate all the important details clearly with the full sound of the microphone. Experience the maxmimum of professional sound optimised for gaming with the MMX 300 PRO.', 1999, 'p38.jpeg', 1, 46, 4.65, 464),
(39, 'Shure SE215 PRO', 1, 14, 'Sound Isolating™ earphones with detachable cable (optional wireless). Blocks 37dB ambient noise, delivers deep bass via dynamic driver. Includes zippered case and fit kit with multiple sleeves.', 658, 'p39.jpeg', 1, 357, 4.8, 1176),

(41, 'Razer Barracuda X', 1, 15, 'Multi-platform wireless headset (PC/PS/Switch/Android) with SmartSwitch Dual Wireless (2.4GHz + BT 5.2). Equips TriForce 40mm drivers and detachable HyperClear Cardioid Mic (Discord-certified). 50-hour battery, 250g weight, and breathable memory foam. Includes 3.5mm wired mode.', 999, 'p41.jpeg', 1, 2334, 4.55, 11656),
(42, 'Logitech PRO X 2.0', 1, 16, 'Pro-grade wireless headset with 50mm graphene drivers for ultra-low distortion. Features LIGHTSPEED wireless (<1ms latency), DTS:X 2.0 surround, and Blue VO!CE mic tech. 50-hour battery, swivel-to-mute mic, and choice of leatherette/velour pads.', 1399, 'p42.jpeg', 1, 882, 4.7, 6172),
(43, 'Logitech A20', 1, 16, 'Console-focused wireless headset (PS/Xbox/PC) with ASTRO Audio V2 tuning. 15m range via USB dongle, 15+ hour battery, and flip-to-mute mic. Lightweight design with cloth ear cushions.', 879, 'p43.jpeg', 1, 1486, 4.7, 6530),
(44, 'Shokz OpenRun Pro 2 S820', 1, 17, 'Premium bone-conduction headphones with TurboPitch™ tech for enhanced bass. Open-ear design (IP55) ensures situational awareness. 10hr battery, dual noise-canceling mics, and titanium frame. 5min charge = 1.5hrs.', 1268, 'p44.jpeg', 1, 1692, 4.95, 10727),
(45, 'Shokz OpenDots ONE', 1, 17, 'True wireless open-ear buds with DirectPitch™ sound tech. Ear-hook design (IP54) keeps ears free. Features AI call noise cancellation, 6hr battery (+22hr case), and touch controls.', 1298, 'p45.jpeg', 1, 378, 4.95, 2456);

INSERT INTO products (
    productID, productName, categoryID, brandID,
    descri, price, img, currentStatus,
    inventoryCount, rating, sales
) VALUES
(51, 'Lenovo Yoga Pro 14s 2024 (Ryzen Edition)', 2, 19, "The Lenovo YOGA Pro 14s 2024 features an AMD Ryzen 7 7840HS processor, offering a lightweight and slim design. It boasts a 14.5-inch 3K 'PureSight Pro' display with a 120Hz refresh rate, hardware-level calibration for P3 and sRGB color gamuts, and Eyesafe certification for comfortable viewing. The laptop supports Dolby Vision and comes with a Dolby Atmos speaker setup. It includes a performance-focused cooling system with dual silent fans and two heat pipes, a 1080p FHD IR webcam, and supports 100W PD fast charging. Connectivity options are rich, including HDMI 2.1, USB 3.2, and USB4. Available with up to 32GB LPDDR5X RAM and 1TB PCIe 4.0 SSD.", 5700, 'p51.jpeg', 1, 3500, 4.7, 10000),
(52, 'HP Spectre x360 14 (Core Ultra 5)', 2, 20, "The HP Spectre x360 14 is a versatile 2-in-1 laptop featuring an Intel Core Ultra 5 processor. It's designed for flexibility with its 360-degree hinge, allowing use in laptop, tablet, and tent modes. The device boasts a 14-inch 2.8K OLED display with a 120Hz refresh rate, offering vibrant colors and smooth visuals. It comes with 16GB of RAM and a 512GB SSD. This model emphasizes style, performance, and adaptability for both work and entertainment, featuring HP Presence 2.0 and Thunderbolt 4 connectivity. It's an Intel Evo Platform certified device, ensuring a premium mobile experience with good battery life and responsiveness.", 7500, 'p52.jpeg', 1, 4000, 4.6, 11666),
(53, 'Lenovo Yoga Slim 6 (13th Gen Intel i5 OLED)', 2, 19, "Powered by an Intel Core i5-13500H processor, the Lenovo Yoga Slim 6 offers a balance of performance and portability. It features a 14-inch WUXGA OLED display with 400 nits brightness and 100% DCI-P3 color gamut, providing stunning visuals. This thin (1.49cm) and light (1.35kg) laptop is crafted from aluminum and includes a backlit keyboard. It comes with 16GB LPDDR5x RAM and a 512GB SSD. Connectivity includes Wi-Fi 6E and Bluetooth 5.3, alongside Thunderbolt 4 ports. The 65Wh battery aims to deliver up to 7 hours of usage. It's designed for users seeking a premium display and solid performance in a compact form factor.", 6800, 'p53.jpeg', 1, 2800, 4.5, 8333),
(54, 'ASUS ROG Zephyrus G14 (Ryzen 7, RTX 3060 - Older Model)', 2, 22, "An older configuration of the ROG Zephyrus G14, this model pairs an AMD Ryzen 7 5800HS processor with NVIDIA GeForce RTX 3060 graphics. It features a 14-inch display, often with a high refresh rate (e.g., 144Hz) and Pantone validation for color accuracy, making it suitable for gaming and content creation. Typically equipped with 16GB of RAM and a 1TB SSD, it balances power and portability. ROG Intelligent Cooling helps manage thermals. While not the latest iteration, it still offers strong performance for AAA games and demanding applications in a compact and stylish chassis, often praised for its unique design elements like the AniMe Matrix display on select versions.", 7900, 'p54.jpeg', 1, 6000, 4.7, 18333),
(55, 'Dell XPS 13 (12th Gen Intel i7)', 2, 22, "This Dell XPS 13 model features a 12th Generation Intel Core i7-1260P processor, 16GB of LPDDR5 RAM, and a 1TB SSD. It sports a 13.4-inch Full HD+ (1920x1200) InfinityEdge anti-reflect display with 500 nits brightness. Crafted with CNC-machined aluminum, it offers a premium and lightweight design. Connectivity includes two Thunderbolt 4 (USB Type-C) ports. The laptop is designed for a stunning combination of speed, performance, and premium mobility, with a focus on a compact footprint and long battery life. Dell's Performance application allows users to customize performance modes (quiet, ultra-performance, cool, or optimized).", 7800, 'p55.jpeg', 1, 3200, 4.6, 9666),
(56, 'Lenovo ThinkPad X1 Carbon Gen 11 (i5, 16GB RAM)', 2, 19, "The Lenovo ThinkPad X1 Carbon Gen 11 with an Intel Core i5 (often 13th Gen) and 16GB RAM is a premium business ultrabook. Known for its lightweight yet durable carbon fiber construction, it offers excellent portability. It typically features a 14-inch display, often with options for higher resolution or touch. Security features are robust, including a fingerprint reader and dTPM chip. The keyboard is renowned for its comfort. Connectivity is comprehensive, usually including Thunderbolt 4 ports. Designed for professionals, it emphasizes productivity, security, and reliability with a long battery life, making it ideal for on-the-go work.", 7999, 'p56.jpeg', 1, 2500, 4.8, 7333),
(57, 'HP Envy x360 15 (Ryzen 7, 16GB RAM)', 2, 20, "The HP Envy x360 15, configured with an AMD Ryzen 7 processor and 16GB of RAM, is a versatile 2-in-1 laptop. Its 15.6-inch touchscreen display, often Full HD or higher, can be rotated 360 degrees for use in laptop, tent, stand, or tablet mode. It typically includes a 512GB or 1TB SSD. The Envy line focuses on a premium design with an aluminum chassis, good audio (often tuned by Bang & Olufsen), and a comfortable keyboard. It's well-suited for productivity, creative tasks, and multimedia consumption, offering a good balance of performance, features, and convertibility for users who need adaptability.", 7200, 'p57.jpeg', 1, 4500, 4.5, 13333),
(58, 'Acer Swift X (Ryzen 7, RTX 3050 Ti)', 2, 23, "The Acer Swift X is a lightweight laptop designed for creators, often featuring an AMD Ryzen 7 processor and dedicated NVIDIA GeForce RTX 3050 Ti graphics. This combination provides a good balance of CPU and GPU power for tasks like video editing and graphic design, as well as light gaming, in a portable form factor. It typically comes with 16GB of RAM and a 512GB or 1TB SSD. The display is usually a 14-inch Full HD IPS panel with good color accuracy. The Swift X aims to deliver performance beyond typical ultrabooks without sacrificing portability, targeting students and creative professionals.", 7600, 'p58.jpeg', 1, 3000, 4.4, 9000),
(59, 'Apple MacBook Air 13-inch (M3 chip, 8GB RAM, 256GB SSD)', 2, 1, "The 13-inch MacBook Air with the M3 chip is a super-portable laptop that excels in both work and play. It features a powerful 8-core CPU and up to a 10-core GPU, delivering smooth performance. Lightweight and under half an inch thin, it's designed for on-the-go use. It boasts up to 18 hours of battery life. The 13.6-inch Liquid Retina display supports one billion colors, offering a brilliant visual experience. It includes a 1080p HD camera, three mics, and four speakers with Spatial Audio. Connectivity includes two Thunderbolt ports, a headphone jack, Wi-Fi 6E, Bluetooth 5.3, and a MagSafe charging port.", 8999, 'p59.jpeg', 1, 15000, 4.9, 46666),
(60, 'Dell XPS 13 Plus (13th Gen Intel i7, 16GB RAM, 512GB SSD)', 2, 22, "The Dell XPS 13 Plus, featuring a 13th Gen Intel® Core™ i7-1360P processor, 16GB LPDDR5 RAM, and a 512GB SSD, redefines computing excellence. Its 13.4-inch FHD+ touch display boasts 500 nits brightness and InfinityEdge technology for a stunning visual experience. The Platinum chassis, backlit keyboard, and fingerprint reader exude elegance. It includes Thunderbolt™ 4 ports for versatile connectivity and Intel® Killer™ Wi-Fi 6E. This laptop is engineered for a stunning combination of speed, performance, and premium mobility, with a simplified, modern, and seamless design featuring a zero-lattice keyboard and capacitive touch function row.", 9500, 'p60.jpeg', 1, 4500, 4.7, 13333),
(61, 'Lenovo ThinkPad X1 Carbon Gen 12 (Core Ultra 5, 16GB RAM, 512GB SSD)', 2, 19, "The ThinkPad X1 Carbon Gen 12 is an industry-leading, ultraportable 14-inch laptop powered by Intel® Core™ Ultra processors, like the Ultra 5 135U, with integrated AI capabilities. It offers all-day battery life and instant wake. This model features a 14-inch display (e.g., 1920x1200 IPS), 16GB of RAM, and a 512GB SSD. It includes Dolby Voice®, Dolby Atmos®, and is Zoom-certified for superior conferencing. Constructed with recycled post-industrial and post-consumer content, it maintains its renowned durability. Connectivity includes two USB-C® (Thunderbolt™ 4) ports, USB-A ports, and HDMI 2.1. An optional Nano SIM slot may be available.", 10500, 'p61.jpeg', 1, 3000, 4.8, 9333),
(62, 'HP Spectre x360 14 (Core Ultra 7, 16GB RAM, 1TB SSD)', 2, 20, "Elevate productivity with the HP Spectre x360 14-inch 2-in-1 Laptop PC, powered by the latest Intel® Core™ Ultra 7 155H processor and built on the Intel® Evo™ Platform. It features a stunning 2.8K OLED display with a variable refresh rate up to 120Hz and Eyesafe® certification. This model comes with 16GB LPDDR5 RAM and a 1TB SSD. Experience built-in AI technology, advanced collaboration tools including a 9MP camera with night mode and AI noise reduction, and seamless phone connectivity. Sustainably designed with EPEAT® Gold and ENERGY STAR® certification, using recycled materials.", 11000, 'p62.jpeg', 1, 2800, 4.7, 8333),
(63, 'ASUS ROG Zephyrus G14 (2024 model, Ryzen 9, RTX 4060)', 2, 21, "The ROG Zephyrus G14 is a dynamic and powerful 14-inch gaming laptop. Newer models feature AMD Ryzen™ 9 processors (e.g., 8945HS) and NVIDIA GeForce RTX™ 40-series GPUs (e.g., RTX 4060 or 4070). It often boasts an OLED ROG Nebula Display with rapid response times, vivid resolution (like 3K), and a smooth 120Hz refresh rate. Despite its compact 1.6kg body, it packs serious performance for gaming and content creation. Features include ROG Intelligent Cooling, upgraded woofers for enhanced audio with Dolby Atmos support, and a sleek, portable design. Some configurations offer the unique AniMe Matrix™ display on the lid.", 11500, 'p63.jpeg', 1, 5500, 4.8, 16666),
(64, 'Samsung Galaxy Book4 Pro (Core Ultra 7, 16GB RAM, 14-inch)', 2, 24, "The Samsung Galaxy Book4 Pro 14-inch is a premium thin and light laptop featuring an Intel Core Ultra 7 processor and Intel Arc graphics. It boasts a stunning Dynamic AMOLED 2X display with a high resolution and refresh rate, offering vibrant colors and smooth visuals. With 16GB of RAM and typically a 512GB or 1TB SSD, it provides strong performance for productivity and creative tasks. It emphasizes portability, a sleek design, and integration with the Samsung Galaxy ecosystem. Features often include a responsive keyboard, a large touchpad, and a comprehensive port selection including Thunderbolt 4.", 10800, 'p64.jpeg', 1, 1800, 4.7, 5000),
(65, 'Microsoft Surface Laptop 5 15-inch (Core i7, 16GB RAM, 512GB SSD)', 2, 25, "The Microsoft Surface Laptop 5 15-inch offers a sleek design and a vibrant PixelSense™ touchscreen. Powered by a 12th Gen Intel® Core™ i7 processor built on the Intel® Evo™ platform, it delivers snappy multitasking. This configuration typically includes 16GB of RAM and a 512GB SSD. It provides all-day battery life and features like Windows Hello face sign-in for security. The large 15-inch display is ideal for productivity and split-screen multitasking. It offers a comfortable typing experience and premium build quality, with connectivity including USB-C with Thunderbolt™ 4. It runs Windows 11 and is optimized for Microsoft software.", 9800, 'p65.jpeg', 1, 2200, 4.6, 6666),
(66, 'Lenovo Yoga Pro 9i 14 (Core Ultra 7, RTX 4050, 32GB RAM)', 2, 19, "The Lenovo Yoga Pro 9i 14 (or Slim Pro 9i in some regions) is a creator-focused laptop. This configuration features an Intel Core Ultra 7 processor, NVIDIA GeForce RTX 4050 dedicated graphics, and a generous 32GB of RAM. The 14.5-inch display is often a high-resolution Mini-LED or OLED panel with excellent color accuracy and brightness, ideal for creative workflows. It includes a robust cooling system to maintain performance, a comfortable keyboard, and a premium sound system. Connectivity is comprehensive, with Thunderbolt 4 and other essential ports. It's designed for users needing significant power in a relatively portable package for video editing, graphic design, and other demanding tasks.", 11800, 'p66.jpeg', 1, 1500, 4.7, 4476),

(68, 'Dell XPS 15 (13th Gen i7, RTX 4050, 16GB RAM, 1TB SSD)', 2, 22, "The Dell XPS 15 (e.g., 9530 model) is a powerhouse for creators, featuring a 13th Gen Intel® Core™ i7 processor (like the i7-13700H) and NVIDIA® GeForce RTX™ 4050 Laptop GPU. It comes with 16GB of DDR5 memory and a 1TB PCIe SSD. The stunning 15.6-inch display can be configured with options like a 3.5K OLED touchscreen for incredible color and contrast. Its precision-crafted chassis uses machined aluminum and carbon fiber. Dual fans and advanced thermal design keep it cool under load. It offers a superior audio experience with Waves Nx® 3D audio. Connectivity includes Thunderbolt™ 4 ports and an SD card reader.", 14500, 'p68.jpeg', 1, 3500, 4.7, 12000),
(69, 'Lenovo ThinkPad X1 Carbon Gen 12 (Core Ultra 7 155U, 32GB RAM, 1TB SSD)', 2, 19, "This high-end configuration of the ThinkPad X1 Carbon Gen 12 features an Intel® Core™ Ultra 7 155U processor, 32GB of RAM, and a 1TB SSD. It retains the ultralight and durable carbon fiber chassis with a 14-inch display, possibly an OLED or high-brightness IPS panel with Eyesafe technology. Enhanced security features include a fingerprint reader and Discrete TPM 2.0. The laptop is designed for professionals demanding top-tier performance, portability, and all-day battery life. It includes advanced audio with Dolby Voice® and Dolby Atmos®, and an improved camera system. Connectivity is robust with Thunderbolt™ 4, USB-A, and HDMI.", 15500, 'p69.jpeg', 1, 1800, 4.8, 6000),
(70, 'HP Spectre x360 16 (Core Ultra 7, RTX 4050, 32GB RAM)', 2, 20, "The HP Spectre x360 16 is a larger premium 2-in-1, offering a 16-inch high-resolution touchscreen (often OLED). This configuration would typically feature an Intel Core Ultra 7 processor, potentially paired with Intel Arc graphics or a discrete NVIDIA GeForce RTX 4050 for enhanced creative power. With 32GB of RAM and a 1TB or 2TB SSD, it's built for demanding tasks and multitasking. It maintains the Spectre's luxurious design, 360-degree hinge, and advanced features like a high-quality webcam with AI enhancements, Bang & Olufsen audio, and comprehensive security options. It's designed for users who want a large, versatile display and strong performance.", 14000, 'p70.jpeg', 1, 1200, 4.7, 3000),
(71, 'ASUS ROG Zephyrus G16 (Core Ultra 9, RTX 4070, 16GB RAM)', 2, 21, "The ROG Zephyrus G16 blends portability with potent gaming and creative performance. This configuration might feature an Intel Core Ultra 9 processor and an NVIDIA GeForce RTX 4070 Laptop GPU. It typically boasts a stunning ROG Nebula Display, often OLED or Mini-LED, with a high refresh rate (e.g., 240Hz) and excellent color accuracy on its 16-inch screen. Despite its power, it maintains a relatively slim and light chassis. Advanced cooling solutions like liquid metal and tri-fan technology are common. It includes a premium audio system, a comfortable keyboard, and a comprehensive port selection. Ideal for gamers and creators needing top performance on the go.", 16500, 'p71.jpeg', 1, 2800, 4.8, 8023),
(72, 'Samsung Galaxy Book4 Ultra (Core Ultra 7 155H, RTX 4050, 16GB RAM, 1TB SSD)', 2, 24, "The Samsung Galaxy Book4 Ultra with an Intel Core Ultra 7 155H processor and NVIDIA GeForce RTX 4050 GPU is a powerful yet relatively slim laptop. It features a 16-inch Dynamic AMOLED 2X touchscreen display with WQXGA+ (2880x1800) resolution and a 120Hz refresh rate, offering exceptional visuals. This model comes with 16GB LPDDR5X RAM and a 1TB SSD. It runs Windows 11 Home and includes quad speakers by AKG with Dolby Atmos, a Full HD webcam, and a backlit keyboard. Samsung Knox enhances security. It's designed for demanding tasks, creative work, and gaming, balancing performance with a premium, portable design.", 17500, 'p72.jpeg', 1, 1000, 4.7, 3000),
(73, 'Microsoft Surface Laptop Studio 2 (i7, RTX 4050, 16GB RAM, 512GB SSD)', 2, 25, "The Surface Laptop Studio 2 is a versatile 2-in-1 convertible designed for creators and professionals. This configuration features an Intel Core i7-13700H processor, NVIDIA GeForce RTX 4050 Laptop GPU, 16GB LPDDR5X RAM, and a 512GB SSD. Its unique 14.4-inch PixelSense™ Flow touchscreen (2400x1600) has a 120Hz refresh rate and can transition between laptop, stage, and studio modes. It includes two Thunderbolt 4 ports and a Precision Haptic touchpad. Designed for demanding workloads, it offers a blend of power, flexibility, and a premium build with an aluminum chassis. It supports Surface Slim Pen 2 for an enhanced creative experience.", 17000, 'p73.jpeg', 1, 900, 4.6, 2600),
(74, 'Gigabyte AERO 16 OLED (i7-13700H, RTX 4070, 16GB RAM, 1TB SSD)', 2, 26, "The Gigabyte AERO 16 OLED is a creator-focused laptop featuring a 13th Gen Intel Core i7-13700H processor and an NVIDIA GeForce RTX 4070 Laptop GPU with 8GB GDDR6. It boasts a stunning 16.0-inch 4K UHD+ (3840x2400) OLED display with a 16:10 aspect ratio, VESA DisplayHDR 600 True Black, and 100% DCI-P3 color gamut, TÜV Rheinland-certified for eye comfort. This model includes 16GB of DDR5 RAM and a 1TB Gen4 M.2 SSD. Connectivity features Intel Wi-Fi 6E, Bluetooth 5.2, and Thunderbolt 4. DTS:X Ultra Audio Technology provides an immersive sound experience. It's designed for professionals needing exceptional visual fidelity and strong performance for creative applications.", 15800, 'p74.jpeg', 1, 700, 4.7, 2000),
(75, 'Apple MacBook Pro 14-inch (M3 Pro chip - base, 18GB RAM, 512GB SSD)', 2, 1, "The 14-inch MacBook Pro with the base M3 Pro chip (e.g., 11-core CPU, 14-core GPU) offers phenomenal performance for demanding pro workflows. It comes with 18GB of unified memory and a 512GB SSD. The stunning Liquid Retina XDR display features extreme dynamic range and ProMotion technology for adaptive refresh rates up to 120Hz. It boasts an advanced thermal system, extensive connectivity including Thunderbolt / USB 4 ports, HDMI, and an SDXC card slot. With exceptional battery life, a 1080p FaceTime HD camera, a studio-quality three-mic array, and a six-speaker sound system, it's built for professionals in video editing, 3D rendering, and software development.", 16999, 'p75.jpeg', 1, 4000, 4.9, 12000),
(76, 'Dell XPS 17 (13th Gen i7, RTX 4070, 32GB RAM, 1TB SSD)', 2, 22, "The Dell XPS 17 (e.g., 9730 model) is a larger creative powerhouse. This configuration typically features a 13th Gen Intel Core i7 processor (e.g., i7-13700H), NVIDIA GeForce RTX 4070 Laptop GPU, 32GB of DDR5 RAM, and a 1TB SSD. Its expansive 17.0-inch InfinityEdge display (often 4K+ UHD+ option) offers an immersive canvas for creative work. The advanced thermal design with a vapor chamber helps maintain performance. It includes a four-speaker design tuned by multi-Grammy Award® winning producer Jack Joseph Puig, Thunderbolt™ 4 ports, and an SD card reader. It's built for users who need maximum screen real estate and desktop-level performance in a portable form factor.", 21000, 'p76.jpeg', 1, 1500, 4.7, 3342),
(77, 'Lenovo ThinkPad P1 Gen 6 (i7, GeForce, 32GB RAM)', 2, 19, "The Lenovo ThinkPad P1 Gen 6 is a thin and light mobile workstation. Configurations can include high-performance Intel Core i7 or i9 processors and professional NVIDIA RTX A-series or high-end GeForce RTX graphics. With 32GB of RAM (often expandable) and fast NVMe SSD storage (e.g., 1TB or 2TB), it's designed for demanding tasks like CAD, 3D modeling, and AI development. It features a 16-inch display, often with options for 4K OLED or high-resolution IPS panels with excellent color accuracy. Despite its power, it maintains a relatively slim profile. It includes robust security features, legendary ThinkPad reliability, and comprehensive connectivity.", 22000, 'p77.jpeg', 1, 800, 4.8, 2850),
(78, 'HP ZBook Studio G10 (Core i9, NVIDIA RTX Ada Gen, 32GB RAM)', 2, 20, "The HP ZBook Studio G10 is a sleek mobile workstation designed for creative professionals. It can be configured with Intel Core i7 or i9 H-series processors and professional NVIDIA RTX Ada Generation Laptop GPUs (e.g., RTX 3000 Ada or higher). It supports up to 64GB of RAM and multiple TBs of NVMe storage. The 16-inch HP DreamColor display (optional) offers exceptional color accuracy. It balances performance with a thin and light design, featuring advanced thermals, Bang & Olufsen audio, and robust security features including HP Wolf Security for Business. It's ISV certified for professional applications, ensuring reliability for demanding creative workflows.", 23500, 'p78.jpeg', 1, 600, 4.7, 1943),
(79, 'ASUS ROG Zephyrus Duo 16 (Ryzen 9, RTX 4080, 32GB RAM)', 2, 21, "The ROG Zephyrus Duo 16 is a unique dual-screen gaming and creator laptop. It typically features a high-end AMD Ryzen 9 processor and an NVIDIA GeForce RTX 4080 Laptop GPU. The main 16-inch display (often Mini-LED Nebula HDR) is complemented by a secondary ROG ScreenPad Plus touchscreen that rises above the keyboard. With 32GB of DDR5 RAM and fast SSD storage, it offers immense multitasking and gaming power. Advanced AAS Plus 2.0 cooling with liquid metal ensures optimal performance. It includes a per-key RGB keyboard, six speakers with Dolby Atmos, and comprehensive connectivity. Ideal for streamers, creators, and gamers who can leverage the dual-screen setup.", 24500, 'p79.jpeg', 1, 1200, 4.8, 3968),
(80, 'Samsung Galaxy Book4 Ultra (Core Ultra 9 185H, RTX 4070, 32GB RAM, 1TB SSD)', 2, 24, "This top-tier Samsung Galaxy Book4 Ultra features the powerful Intel Core Ultra 9 185H processor, an NVIDIA GeForce RTX 4070 Laptop GPU, 32GB of LPDDR5X RAM, and a 1TB NVMe SSD. The 16-inch Dynamic AMOLED 2X touchscreen offers a stunning 2880x1800 resolution and 120Hz refresh rate. It's designed for users who need maximum performance for AI-supported tasks, creative image/video editing, and gaming. The laptop remains cool under pressure due to its advanced cooling system. It includes Samsung Knox for security, a Full HD webcam, quad AKG speakers with Dolby Atmos, and a long-lasting battery with fast charging.", 22500, 'p80.jpeg', 1, 700, 4.8, 2186),
(81, 'Microsoft Surface Laptop Studio 2 (i7, RTX 4060, 32GB RAM, 1TB SSD)', 2, 25, "A higher-end configuration of the Surface Laptop Studio 2, this model packs an Intel Core i7-13700H (or i7-13800H for business models), NVIDIA GeForce RTX 4060 Laptop GPU, 32GB LPDDR5X RAM, and a 1TB SSD. The 14.4-inch PixelSense™ Flow display (2400x1600, 120Hz) offers incredible versatility with its unique hinge. It's built for demanding creative applications, coding, and content creation, offering over 2x more power than its predecessor. Features include a studio camera with AI enhancements, Thunderbolt 4 ports, and up to 18 hours of battery life. It provides a seamless experience for professionals needing power, portability, and adaptability.", 21500, 'p81.jpeg', 1, 600, 4.7, 1868),
(82, 'Gigabyte AERO 16 OLED (i9-13900H, RTX 4070, 32GB RAM, 2TB SSD)', 2, 26, "This premium Gigabyte AERO 16 OLED configuration features the powerful Intel Core i9-13900H processor, NVIDIA GeForce RTX 4070 Laptop GPU, 32GB of DDR5 RAM, and a spacious 2TB Gen4 M.2 SSD. The centerpiece is its 16.0-inch 4K UHD+ (3840x2400) OLED display, factory-calibrated and X-Rite™ certified for exceptional color accuracy, covering 100% DCI-P3. It's designed for creative professionals who demand top-tier performance and visual fidelity for video editing, 3D rendering, and graphic design. Thunderbolt 4, Wi-Fi 6E, and a robust port selection ensure excellent connectivity. The CNC-milled aluminum chassis provides a sleek and durable build.", 20500, 'p82.jpeg', 1, 500, 4.8, 1500),
(83, 'Apple MacBook Pro 14-inch (M3 Max chip - base, 36GB RAM, 1TB SSD)', 2, 1, "The 14-inch MacBook Pro with the entry-level M3 Max chip (e.g., 14-core CPU, 30-core GPU) delivers extraordinary performance for the most intensive tasks. It comes standard with 36GB of unified memory and a 1TB SSD. The Liquid Retina XDR display is industry-leading. This machine is built for professionals pushing the limits of creativity and innovation, such as 8K video editing, complex 3D rendering, and demanding scientific applications. It offers extensive battery life, a sophisticated thermal system, and a full suite of pro ports. The M3 Max chip provides a massive leap in GPU performance and memory bandwidth.", 24000, 'p83.jpeg', 1, 2000, 4.9, 6251),
(84, 'Razer Blade 15 Advanced (13th Gen i7, RTX 4070, QHD 240Hz)', 2, 15, "The Razer Blade 15 Advanced Model typically features a 13th Gen Intel Core i7 or i9 HX-series processor and an NVIDIA GeForce RTX 4070 or RTX 4080 Laptop GPU. It's known for its 15.6-inch QHD (2560x1440) display with a fast 240Hz refresh rate, providing smooth and sharp visuals for gaming. It usually comes with 16GB or 32GB of DDR5 RAM and a 1TB PCIe Gen4 SSD. The CNC aluminum unibody chassis is iconic for its sleek, black design. Per-key RGB Chroma lighting, a vapor chamber cooling system, and Thunderbolt 4 ports are standard. It's a premium gaming laptop that balances high performance with a relatively compact and stylish form factor.", 23000, 'p84.jpeg', 1, 1000, 4.7, 3000),
(85, 'Huawei MateBook X Pro 2024 (Core Ultra 9 185H, 32GB RAM, 2TB SSD)', 2, 7, "The Huawei MateBook X Pro 2024 is an ultra-premium and lightweight notebook. This top configuration features an Intel Core Ultra 9 185H processor, 32GB of RAM, and a 2TB NVMe PCIe SSD. It boasts a stunning 14.2-inch flexible OLED display with a 3120x2080 resolution, 120Hz refresh rate, and 1000 nits peak brightness. The laptop is incredibly thin and light (around 980g). It incorporates Huawei's Pangu AI model for smart features. The device uses a premium magnesium alloy material and features a 3D metamaterial antenna for enhanced network speed. It has a 70Wh battery with 140W fast charging.", 18500, 'p85.jpeg', 1, 900, 4.8, 2030),
(86, 'Apple MacBook Pro 16-inch (M3 Pro chip - upper, 36GB RAM, 1TB SSD)', 2, 1, "The 16-inch MacBook Pro with an upgraded M3 Pro chip (e.g., 12-core CPU, 18-core GPU) and 36GB of unified memory offers a significant boost in performance for demanding creative and professional applications. It includes a 1TB SSD. The larger Liquid Retina XDR display provides an expansive and brilliant canvas. It features an advanced thermal system, exceptional battery life, a 1080p FaceTime HD camera, a studio-quality mic array, and a high-fidelity six-speaker sound system. This model is ideal for users who need more screen real estate and sustained performance for tasks like complex video editing, music production, and 3D design.", 26000, 'p86.jpeg', 1, 2500, 4.9, 7367),
(87, 'Dell Alienware m18 (13th Gen i9, RTX 4080, 32GB RAM, QHD+ 165Hz)', 2, 22, "The Alienware m18 is a flagship gaming laptop. This configuration would feature a top-tier Intel Core i9 processor (13th or 14th Gen HX-series) and an NVIDIA GeForce RTX 4080 or RTX 4090 Laptop GPU. It boasts an 18-inch QHD+ (2560x1600) display with a 165Hz or higher refresh rate and G-SYNC support. Typically equipped with 32GB of DDR5 RAM (often expandable) and 1TB or 2TB of SSD storage (often in RAID 0). Alienware's Cryo-tech™ cooling technology with Element 31 thermal interface material and a vapor chamber ensures sustained performance. It features an AlienFX RGB keyboard, premium audio, and a distinctive Legend 3.0 industrial design.", 28000, 'p87.jpeg', 1, 1000, 4.8, 3000),
(88, 'ASUS ROG Strix SCAR 18 (i9-14900HX, RTX 4090, 32GB RAM, 2TB SSD)', 2, 21, "The ROG Strix SCAR 18 is a top-of-the-line gaming laptop designed for esports and hardcore gamers. It features the Intel Core i9-14900HX processor and NVIDIA GeForce RTX 4090 Laptop GPU. The 18-inch ROG Nebula HDR Display (often Mini-LED) offers QHD+ resolution and a 240Hz refresh rate. This model comes with 32GB of DDR5 RAM and a 2TB PCIe 4.0 SSD. ROG Intelligent Cooling with Conductonaut Extreme liquid metal on both CPU and GPU, and a Tri-Fan Technology ensures maximum sustained performance. It includes a per-key RGB keyboard, customizable Armor Caps, and a semi-translucent chassis design. It's built for ultimate gaming dominance.", 33000, 'p88.jpeg', 1, 800, 4.9, 2500),
(89, 'Razer Blade 16 (i9 HX, RTX 4080, Dual-mode Mini-LED)', 2, 15, "The Razer Blade 16 offers a unique 16-inch dual-mode Mini-LED display that can switch between UHD+ 120Hz (for creative work) and FHD+ 240Hz (for gaming). It's powered by an Intel Core i9 HX-series processor and NVIDIA GeForce RTX 4080 or RTX 4090 Laptop GPU. Typically configured with 32GB of DDR5 RAM and 1TB or 2TB SSD. The CNC aluminum chassis, per-key RGB lighting, and vapor chamber cooling are hallmarks of the Blade series. It offers a blend of extreme performance for gaming and content creation with a highly innovative display technology in a relatively sleek package. Thunderbolt 4 and a comprehensive port selection are included.", 31000, 'p89.jpeg', 1, 700, 4.8, 2000),
(90, 'Lenovo ThinkPad P16 Gen 2 (i9 HX, RTX 5000 Ada, 64GB RAM)', 2, 19, "The ThinkPad P16 Gen 2 is a no-compromise 16-inch mobile workstation. This high-end configuration would feature an Intel Core i9 HX-series processor and a powerful NVIDIA RTX 5000 Ada Generation Laptop GPU with 16GB VRAM. It can be equipped with 64GB or more of DDR5 RAM and multiple terabytes of PCIe Gen4 NVMe SSD storage, possibly in RAID. The display options include stunning 4K OLED or high-brightness IPS panels with excellent color fidelity. It features an advanced cooling system, ISV certifications, robust security features, and the legendary ThinkPad durability and keyboard. It's built for the most demanding professional workloads.", 35000, 'p90.jpeg', 1, 400, 4.9, 1243),
(91, 'MSI Titan GT77 HX (13th Gen i9, RTX 4090, 4K Mini-LED 144Hz)', 2, 27, "The MSI Titan GT77 HX is one of the most powerful desktop replacement gaming laptops. It features a top-tier Intel Core i9 HX-series processor (13th or 14th Gen) and the flagship NVIDIA GeForce RTX 4090 Laptop GPU with maximum TGP. The display is often a 17.3-inch 4K Mini-LED panel with a 144Hz refresh rate, offering incredible visuals. It can support up to 128GB of DDR5 RAM and multiple M.2 SSDs for massive storage. The Cooler Boost Titan cooling system with multiple fans and heat pipes is designed for extreme overclocking. It features a Cherry MX mechanical keyboard, Dynaudio sound system, and extensive connectivity.", 38000, 'p91.jpeg', 1, 500, 4.8, 1500),
(92, 'Apple MacBook Pro 16-inch (M3 Max chip - upper, 48GB RAM, 2TB SSD)', 2, 1, "A highly configured 16-inch MacBook Pro with an upgraded M3 Max chip (e.g., 16-core CPU, 40-core GPU), 48GB or 64GB of unified memory, and a 2TB SSD represents the pinnacle of Apple's laptop performance. This machine is designed for professionals tackling the most extreme workflows, including high-resolution multi-stream video editing, complex 3D animation and rendering, and large-scale scientific computing. The Liquid Retina XDR display, pro connectivity, exceptional battery life, and advanced thermal management enable sustained peak performance. It's a significant investment for users who require uncompromising power and capability in a portable Mac.", 36000, 'p92.jpeg', 1, 1500, 4.9, 4000),
(93, 'Dell Precision 7780 (i9 HX, RTX 5000 Ada, 64GB RAM, 4K PremierColor)', 2, 22, "The Dell Precision 7780 is a top-tier 17.3-inch mobile workstation. This configuration would house an Intel Core i9 HX-series processor, an NVIDIA RTX 5000 Ada Generation Laptop GPU, and 64GB of DDR5 RAM (often ECC options available). It supports multiple terabytes of PCIe Gen4 NVMe SSD storage, with RAID capabilities. The 17.3-inch display can be a 4K PremierColor panel with 100% DCI-P3 coverage, ideal for color-critical work. It features Dell Optimizer for performance tuning, advanced thermals, ISV certifications, and robust security. Built for engineers, data scientists, and content creators who need desktop-grade power and reliability on the go.", 37000, 'p93.jpeg', 1, 300, 4.8, 900),
(94, 'HP Omen Transcend 16 (i9, RTX 4080, Mini-LED, 32GB RAM)', 2, 20, "The HP Omen Transcend 16 is a premium thin and light gaming laptop. This high-end version would feature an Intel Core i9 processor and an NVIDIA GeForce RTX 4080 or RTX 4090 Laptop GPU. A key feature is its 16-inch Mini-LED display, offering high brightness, deep blacks, and excellent HDR performance, often with a 240Hz refresh rate. It comes with 32GB of DDR5 RAM and a fast 2TB SSD. Despite its power, it maintains a slimmer profile than traditional gaming behemoths, focusing on portability without major performance compromises. Advanced OMEN Tempest Cooling technology helps manage heat. It's aimed at gamers who also value a sleek design and content creation capabilities.", 27000, 'p94.jpeg', 1, 600, 4.7, 1600),
(95, 'ASUS ROG Zephyrus M16 (i9, RTX 4090, Nebula HDR Display, 32GB RAM)', 2, 21, "The ROG Zephyrus M16 is a powerful and stylish laptop for gamers and creators. Top configurations feature an Intel Core i9 processor and NVIDIA GeForce RTX 4080 or RTX 4090 Laptop GPU. It's known for its stunning 16-inch ROG Nebula HDR Display (often Mini-LED) with high resolution, high refresh rate, and Pantone validation. With 32GB of DDR5 RAM and up to 2TB SSD, it handles demanding tasks with ease. The ErgoLift hinge improves cooling and typing comfort. Six speakers with Dolby Atmos provide immersive audio. It balances high-end performance with a relatively slim and sophisticated design, often featuring the AniMe Matrix on the lid.", 29000, 'p95.jpeg', 1, 900, 4.8, 2367),
(96, 'Lenovo Legion Pro 7i Gen 9 (i9 HX, RTX 4080, 32GB RAM)', 2, 19, "The Lenovo Legion Pro 7i is a high-performance gaming laptop. Top-tier models feature an Intel Core i9 HX-series processor and an NVIDIA GeForce RTX 4080 or RTX 4090 Laptop GPU, pushed to high TGPs for maximum performance. It typically has a 16-inch QHD+ (2560x1600) display with a high refresh rate (e.g., 240Hz) and G-SYNC. Configured with 32GB of DDR5 RAM and 1TB or 2TB SSD. The Legion Coldfront cooling system with a vapor chamber and liquid metal ensures optimal thermals. It includes a TrueStrike keyboard with per-key RGB, Nahimic audio, and a robust build quality. It's designed for competitive gamers and power users.", 27500, 'p96.jpeg', 1, 1100, 4.8, 3322),
(97, 'Gigabyte AORUS 17X (i9 HX, RTX 4090, QHD 240Hz, 32GB RAM)', 2, 26, "The Gigabyte AORUS 17X is a flagship gaming laptop built for extreme performance. It packs an Intel Core i9 HX-series processor and an NVIDIA GeForce RTX 4080 or RTX 4090 Laptop GPU. The 17.3-inch display is typically a QHD (2560x1440) panel with a 240Hz refresh rate and excellent color accuracy. It comes with 32GB of DDR5 RAM and fast PCIe Gen4 SSD storage. The WINDFORCE Infinity cooling system with multiple fans and heat pipes ensures stable performance under heavy loads. It features a mechanical keyboard option, vibrant RGB lighting, and a premium audio setup. It's aimed at enthusiast gamers who demand desktop-level power in a portable (though large) form factor.", 30000, 'p97.jpeg', 1, 600, 4.7, 2768),
(98, 'Razer Blade 18 (i9 HX, RTX 4090, 18-inch QHD+ 240Hz, 64GB RAM)', 2, 15, "The Razer Blade 18 is Razer's largest and most powerful laptop, designed as a true desktop replacement. It features an Intel Core i9 HX-series processor and the NVIDIA GeForce RTX 4090 Laptop GPU. The massive 18-inch QHD+ (2560x1600) display offers a 240Hz refresh rate. This configuration can support up to 64GB of DDR5 RAM and dual SSDs for ample storage. It boasts an advanced vapor chamber cooling system, a THX Spatial Audio speaker system, and per-key Chroma RGB lighting. Despite its size, it maintains Razer's signature sleek CNC aluminum design. It's for users who want ultimate gaming and creative performance without compromise.", 39000, 'p98.jpeg', 1, 400, 4.8, 1220),
(99, 'Dell Alienware x16 R2 (Core Ultra 9, RTX 4090, 32GB RAM, QHD+ 240Hz)', 2, 22, "The Alienware x16 R2 is a slimmer and more refined high-end gaming laptop. It can be configured with an Intel Core Ultra 9 processor and an NVIDIA GeForce RTX 4090 Laptop GPU. The 16-inch display is typically QHD+ (2560x1600) with a 240Hz refresh rate and ComfortView Plus. It usually comes with 32GB of LPDDR5X RAM and up to 4TB of SSD storage. Alienware's Cryo-tech™ cooling, including Element 31, is utilized. The AlienFX lighting system with a distinctive rear stadium loop and micro-LEDs on the touchpad (on some configs) adds to its unique aesthetic. It aims to deliver top-tier gaming performance in a more portable and stylish chassis than traditional Alienware m-series.", 34000, 'p99.jpeg', 1, 500, 4.8, 1358),
(100, 'MSI Stealth 17 Studio (i9, RTX 4090, 4K Mini-LED, 64GB RAM)', 2, 27, "The MSI Stealth 17 Studio is a high-performance laptop that balances gaming prowess with creator-friendly features in a relatively slim chassis. This top-end configuration would feature an Intel Core i9 processor, NVIDIA GeForce RTX 4090 Laptop GPU, and a stunning 17.3-inch 4K Mini-LED display with high refresh rates and excellent color accuracy. It can be equipped with up to 64GB of DDR5 RAM and fast NVMe SSDs. The Cooler Boost 5 thermal solution helps maintain performance. It often includes a SteelSeries per-key RGB keyboard, Dynaudio sound system, and Thunderbolt 4. It's NVIDIA Studio certified, making it suitable for both demanding games and intensive creative workloads.", 36500, 'p100.jpeg', 1, 350, 4.7, 1000);
-- 重建 carts，只用 userID 作为“购物车 ID”，并用 (userID,productID) 做主键
CREATE TABLE IF NOT EXISTS carts (
    userID     BIGINT UNSIGNED NOT NULL,     -- 用户 ID，也是购物车标识
    productID  CHAR(12)        NOT NULL,     -- 商品 ID
    quantity   INT UNSIGNED    NOT NULL DEFAULT 1 CHECK (quantity > 0),
    createdAt  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (userID, productID),         -- 复合主键
    INDEX idx_user (userID),

    CONSTRAINT fk_carts_user
      FOREIGN KEY (userID) REFERENCES users(id)
      ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_carts_product
      FOREIGN KEY (productID) REFERENCES products(productID)
      ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB CHARSET=utf8mb4;

INSERT INTO carts (userID, productID, quantity, createdAt) VALUES
  (2, '11', 1, '2024-05-01 10:30:00'),
  (2, '37', 1, '2024-05-01 11:30:00'),
  (2, '27', 1, '2024-05-01 12:30:00');

-- 推荐表也同步调整（如果需要）
CREATE TABLE IF NOT EXISTS recommend_home (
    userID     BIGINT UNSIGNED NOT NULL,  -- 只使用用户ID
    productID  CHAR(12)        NOT NULL,
    rankNo     TINYINT         NOT NULL,
    algoTag    VARCHAR(20)     NOT NULL,
    score      FLOAT           NULL,
    createdAt  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(userID, algoTag, rankNo),  -- 主键调整
    CONSTRAINT fk_recommend_user
      FOREIGN KEY (userID) REFERENCES users(id)
      ON DELETE CASCADE
) ENGINE=InnoDB CHARSET=utf8mb4;

-- 订单表（整合自 checkout.sql）
CREATE TABLE IF NOT EXISTS orders (
    order_id        CHAR(36)      PRIMARY KEY,
    userID         BIGINT UNSIGNED NOT NULL,
    total_amount    DECIMAL(10,2)  NOT NULL,
    status          ENUM('pending', 'paid', 'failed', 'shipped', 'completed') DEFAULT 'pending',
    payment_method  ENUM('credit_card') DEFAULT 'credit_card',
    shipping_method VARCHAR(50)    NOT NULL,
    phone           VARCHAR(20)    NOT NULL,
    street_address  VARCHAR(255)   NOT NULL,
    city            VARCHAR(50)    NOT NULL,
    postal_code     VARCHAR(20)    NOT NULL,
    country         ENUM('Hong Kong SAR', 'China', 'United States') NOT NULL,
    created_at      DATETIME       DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (userID) REFERENCES users(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    INDEX idx_orders_user (userID)
) ENGINE=InnoDB CHARSET=utf8mb4;

-- 订单商品项表
CREATE TABLE IF NOT EXISTS order_items (
    order_item_id  BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    order_id       CHAR(36)      NOT NULL,
    productID      CHAR(12)      NOT NULL,
    quantity       INT UNSIGNED  NOT NULL CHECK(quantity > 0),
    price          DECIMAL(10,2) NOT NULL CHECK(price >= 0.01),
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
    FOREIGN KEY (productID) REFERENCES products(productID) ON DELETE RESTRICT,
    INDEX idx_order_items_product (productID)
) ENGINE=InnoDB CHARSET=utf8mb4;

-- 支付记录表
CREATE TABLE IF NOT EXISTS payments (
    payment_id      CHAR(36)      PRIMARY KEY,
    order_id        CHAR(36)      NOT NULL,
    amount          DECIMAL(10,2) NOT NULL,
    status          ENUM('pending', 'succeeded', 'failed') DEFAULT 'pending',
    card_last4      CHAR(4)       NOT NULL,
    transaction_id  VARCHAR(255)  NOT NULL UNIQUE,
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
    INDEX idx_payments_order (order_id)
) ENGINE=InnoDB CHARSET=utf8mb4;

-- Example query: Validate data integrity for Headphones category
SELECT
    p.productID,
    p.productName,
    c.categoryName,
    b.brandName,
    p.price,
    p.inventoryCount,
    CONCAT('/images/products/', p.img) AS ImageUrl
FROM products p
JOIN category c ON p.categoryID = c.categoryID
JOIN brand    b ON p.brandID    = b.brandID
WHERE c.categoryID = 1;