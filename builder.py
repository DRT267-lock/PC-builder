from db import Database
# builder.py – автоматический подбор конфигурации
async def build_pc(db: Database, usage: str, budget: int) -> dict:
    # === Tiered stub implementation with usage consideration ===
    u = usage.lower()
    # Office builds
    if u in ["работа", "офис"]:
        if budget < 20000:
            build = {
                'cpu': {'name': 'Intel Pentium Gold G6400', 'price': 6000},
                'motherboard': {'name': 'ASUS PRIME H410M', 'price': 5000},
                'ram': {'name': '8GB DDR4', 'price': 2000},
                'gpu': None,
                'storage': {'name': '256GB SSD', 'price': 3000},
                'psu': {'name': '450W PSU', 'price': 2000},
                'case': {'name': 'Budget Case', 'price': 1500},
                'cooler': None,
            }
        elif budget < 50000:
            build = {
                'cpu': {'name': 'Intel Core i5-10400', 'price': 12000},
                'motherboard': {'name': 'MSI B560M PRO', 'price': 8000},
                'ram': {'name': '16GB DDR4', 'price': 4000},
                'gpu': None,
                'storage': {'name': '512GB SSD', 'price': 5000},
                'psu': {'name': '550W Bronze PSU', 'price': 3500},
                'case': {'name': 'Mid Tower Case', 'price': 2500},
                'cooler': None,
            }
        else:
            build = {
                'cpu': {'name': 'Intel Core i7-11700', 'price': 20000},
                'motherboard': {'name': 'ASUS TUF Z590-PLUS', 'price': 15000},
                'ram': {'name': '32GB DDR4', 'price': 8000},
                'gpu': None,
                'storage': {'name': '1TB NVMe SSD', 'price': 10000},
                'psu': {'name': '650W Gold PSU', 'price': 5000},
                'case': {'name': 'Premium Case', 'price': 5000},
                'cooler': None,
            }
    # Rendering/3D builds
    elif u in ["рендеринг", "3d", "рендеринг/3d"]:
        if budget < 30000:
            build = {
                'cpu': {'name': 'AMD Ryzen 5 3600', 'price': 12000},
                'motherboard': {'name': 'Gigabyte B450M DS3H', 'price': 6000},
                'ram': {'name': '16GB DDR4', 'price': 4000},
                'gpu': {'name': 'NVIDIA GTX 1660 Super', 'price': 20000},
                'storage': {'name': '512GB SSD', 'price': 5000},
                'psu': {'name': '550W Bronze PSU', 'price': 3500},
                'case': {'name': 'Mid Tower Case', 'price': 2500},
                'cooler': {'name': 'Stock Cooler', 'price': 800},
            }
        elif budget < 70000:
            build = {
                'cpu': {'name': 'AMD Ryzen 7 5800X', 'price': 25000},
                'motherboard': {'name': 'MSI B550-A PRO', 'price': 12000},
                'ram': {'name': '32GB DDR4', 'price': 8000},
                'gpu': {'name': 'NVIDIA RTX 3060 Ti', 'price': 30000},
                'storage': {'name': '1TB NVMe SSD', 'price': 10000},
                'psu': {'name': '650W Gold PSU', 'price': 5000},
                'case': {'name': 'Mid Tower Case', 'price': 2500},
                'cooler': {'name': 'Aftermarket Air Cooler', 'price': 3000},
            }
        else:
            build = {
                'cpu': {'name': 'AMD Ryzen 9 5900X', 'price': 35000},
                'motherboard': {'name': 'ASUS TUF X570-PLUS', 'price': 20000},
                'ram': {'name': '64GB DDR4', 'price': 16000},
                'gpu': {'name': 'NVIDIA RTX 3080', 'price': 60000},
                'storage': {'name': '2TB NVMe SSD', 'price': 20000},
                'psu': {'name': '750W Gold PSU', 'price': 7000},
                'case': {'name': 'Premium Case', 'price': 5000},
                'cooler': {'name': 'High-End Air Cooler', 'price': 5000},
            }
    # Gaming/default builds
    else:
        if budget < 20000:
            build = {
                'cpu': {'name': 'Intel Core i3-10100', 'price': 8000},
                'motherboard': {'name': 'ASUS PRIME H410M', 'price': 5000},
                'ram': {'name': '8GB DDR4', 'price': 2000},
                'gpu': {'name': 'NVIDIA GTX 1050 Ti', 'price': 9000},
                'storage': {'name': '256GB SSD', 'price': 3000},
                'psu': {'name': '450W PSU', 'price': 2000},
                'case': {'name': 'Budget Case', 'price': 1500},
                'cooler': {'name': 'Stock Cooler', 'price': 800},
            }
        elif budget < 50000:
            build = {
                'cpu': {'name': 'Intel Core i5-10400F', 'price': 12000},
                'motherboard': {'name': 'MSI B460M PRO', 'price': 7000},
                'ram': {'name': '16GB DDR4', 'price': 4000},
                'gpu': {'name': 'NVIDIA GTX 1660 Super', 'price': 20000},
                'storage': {'name': '500GB SSD', 'price': 5000},
                'psu': {'name': '550W Bronze PSU', 'price': 3500},
                'case': {'name': 'Mid Tower Case', 'price': 2500},
                'cooler': {'name': 'Stock Cooler', 'price': 800},
            }
        else:
            build = {
                'cpu': {'name': 'Intel Core i7-11700K', 'price': 25000},
                'motherboard': {'name': 'ASUS TUF Z590-PLUS', 'price': 15000},
                'ram': {'name': '32GB DDR4', 'price': 8000},
                'gpu': {'name': 'NVIDIA RTX 3070', 'price': 40000},
                'storage': {'name': '1TB NVMe SSD', 'price': 10000},
                'psu': {'name': '650W Gold PSU', 'price': 5000},
                'case': {'name': 'Premium Case', 'price': 5000},
                'cooler': {'name': 'Aftermarket Air Cooler', 'price': 3000},
            }
    # Рассчитываем итоговую цену
    total = sum(item['price'] for item in build.values() if item)
    build['total_price'] = total if total <= budget else budget
    return build
