DROP DATABASE IF EXISTS buyzu;
CREATE DATABASE IF NOT EXISTS buyzu;
USE buyzu;

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
(3, 'Keyboards'),
(4, 'Watches');

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
(7, 'HUAWEI'),
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
(18, 'QCY');

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
(40, 'Razer BlackShark V2 PRO', 1, 15, 'Pro esports wireless headset with Razer™ TriForce Titanium 50mm drivers for competitive audio clarity. Features detachable HyperClear Super Wideband Mic (24-bit/96kHz), THX Spatial Audio, and 70-hour battery. HyperSpeed Wireless (2.4GHz) ensures <40ms latency, while memory foam FlowKnit cushions provide all-day comfort at 320g. Includes FPS-tuned EQ presets.', 1379, 'p40.jpeg', 1, 7155, 4.7, 49331),
(41, 'Razer Barracuda X', 1, 15, 'Multi-platform wireless headset (PC/PS/Switch/Android) with SmartSwitch Dual Wireless (2.4GHz + BT 5.2). Equips TriForce 40mm drivers and detachable HyperClear Cardioid Mic (Discord-certified). 50-hour battery, 250g weight, and breathable memory foam. Includes 3.5mm wired mode.', 999, 'p41.jpeg', 1, 2334, 4.55, 11656),
(42, 'Logitech PRO X 2.0', 1, 16, 'Pro-grade wireless headset with 50mm graphene drivers for ultra-low distortion. Features LIGHTSPEED wireless (<1ms latency), DTS:X 2.0 surround, and Blue VO!CE mic tech. 50-hour battery, swivel-to-mute mic, and choice of leatherette/velour pads.', 1399, 'p42.jpeg', 1, 882, 4.7, 6172),
(43, 'Logitech A20', 1, 16, 'Console-focused wireless headset (PS/Xbox/PC) with ASTRO Audio V2 tuning. 15m range via USB dongle, 15+ hour battery, and flip-to-mute mic. Lightweight design with cloth ear cushions.', 879, 'p43.jpeg', 1, 1486, 4.7, 6530),
(44, 'Shokz OpenRun Pro 2 S820', 1, 17, 'Premium bone-conduction headphones with TurboPitch™ tech for enhanced bass. Open-ear design (IP55) ensures situational awareness. 10hr battery, dual noise-canceling mics, and titanium frame. 5min charge = 1.5hrs.', 1268, 'p44.jpeg', 1, 1692, 4.95, 10727),
(45, 'Shokz OpenDots ONE', 1, 17, 'True wireless open-ear buds with DirectPitch™ sound tech. Ear-hook design (IP54) keeps ears free. Features AI call noise cancellation, 6hr battery (+22hr case), and touch controls.', 1298, 'p45.jpeg', 1, 378, 4.95, 2456);

-- Create shopping cart table
CREATE TABLE IF NOT EXISTS carts (
    cartID     BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    sessionID  VARCHAR(255)  NULL,
    userID     BIGINT UNSIGNED NULL,
    productID  CHAR(12)      NOT NULL,
    quantity   INT UNSIGNED  NOT NULL DEFAULT 1 CHECK (quantity > 0),
    createdAt  DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,

    /* 生成列：MariaDB 用 VIRTUAL/PERSISTENT */
    ownerKey VARCHAR(255)
             GENERATED ALWAYS AS (IFNULL(CAST(userID AS CHAR(20)), sessionID))
             VIRTUAL,                          -- ← 改这里

    UNIQUE KEY uk_owner_product (ownerKey, productID),
    INDEX idx_user    (userID),
    INDEX idx_session (sessionID),

    CONSTRAINT fk_carts_product
      FOREIGN KEY (productID) REFERENCES products(productID)
      ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB CHARSET=utf8mb4;

-- Example operation:
INSERT INTO carts (sessionID, productID, quantity, createdAt)
VALUES ('sess_mabhzns8_2b35', '11', 1, '2024-05-01 10:30:00')
ON DUPLICATE KEY UPDATE
        quantity = quantity + VALUES(quantity);

INSERT INTO carts (sessionID, productID, quantity, createdAt)
VALUES ('sess_mabhzns8_2b35', '37', 1, '2024-05-01 11:30:00')
ON DUPLICATE KEY UPDATE
        quantity = quantity + VALUES(quantity);

INSERT INTO carts (sessionID, productID, quantity, createdAt)
VALUES ('sess_mabhzns8_2b35', '27', 1, '2024-05-01 12:30:00')
ON DUPLICATE KEY UPDATE
        quantity = quantity + VALUES(quantity);

INSERT INTO carts (sessionID, productID, quantity, createdAt)
VALUES ('sess_mabhzns8_2b35', '3', 1, '2024-05-01 13:30:00')
ON DUPLICATE KEY UPDATE
        quantity = quantity + VALUES(quantity);

CREATE TABLE IF NOT EXISTS recommend_home (
    userKey   VARCHAR(255) NOT NULL,   -- userID 或 sessionID
    productID CHAR(12)     NOT NULL,
    rankNo    TINYINT      NOT NULL,   -- 1..TOPK
    algoTag   VARCHAR(20)  NOT NULL,   -- baseline / sasrec / mix
    score      FLOAT        NULL,
    createdAt DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(userKey, algoTag, rankNo)
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