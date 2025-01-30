import json
import requests
from configparser import ConfigParser

config = ConfigParser()
config.read('config.ini')
test_imeicheck = config['imeicheck']['sandbox_token']
live_imeicheck = config['imeicheck']['live_token']
serviceId_live = config['imeicheck']['serviceId_live']
serviceId_test = config['imeicheck']['serviceId_test']


def format_json_response(json_response: str) -> str:
    """ Форматирование json для лучшего вида """
    try:
        response = json.loads(json_response)
    except:
        response = json_response
    if isinstance(response, dict) and 'error' in response:
        return json.dumps(response, indent=2)

    properties = response.get('properties', {})
    status = response.get('status', 'unknown')

    formatted_text = (
        '{\n'
        f'  "imei": "{response.get("deviceId", "N/A")}",\n'
        f'  "model": "{properties.get("deviceName", "N/A")}, {properties.get("modelDesc", "N/A")}, {properties.get("apple/modelName", "N/A")}",\n'
        f'  "manufacturer": "{properties.get("apple/region", "N/A")}, {properties.get("modelDesc", "N/A")}",\n'
        f'  "serialNumber": "{properties.get("serial", "N/A")}",\n'
        f'  "status": {{\n'
        f'    "overall": "{status}",\n'
        f'    "gsmaBlacklisted": {properties.get("gsmaBlacklisted", "N/A")},\n'
        f'    "replaced": {properties.get("replaced", "N/A")},\n'
        f'    "refurbished": {properties.get("refurbished", "N/A")}\n'
        f'  }},\n'
        f'  "additionalCharacteristics": {{\n'
        f'    "meid": "{properties.get("meid", "N/A")}",\n'
        f'    "imei2": "{properties.get("imei2", "N/A")}",\n'
        f'    "estPurchaseDate": "{properties.get("estPurchaseDate", "N/A")}",\n'
        f'    "purchaseCountry": "{properties.get("purchaseCountry", "N/A")}",\n'
        f'    "region": "{properties.get("apple/region", "N/A")}",\n'
        f'    "fmiOn": {properties.get("fmiOn", "N/A")},\n'
        f'    "lostMode": {properties.get("lostMode", "N/A")},\n'
        f'    "warrantyStatus": "{properties.get("warrantyStatus", "N/A")}"\n'
        f'    "image": {properties.get("image")}\n'
        f'  }}\n'
        "}"
    )

    return formatted_text


def check_imei(imei: str, on_test: bool) -> str:
    """ Отправка запроса к imeicheck """

    url = 'https://api.imeicheck.net/v1/checks'

    if on_test:
        payload = {
            'deviceId': imei,
            'serviceId': serviceId_test
        }
        headers = {
            'Authorization': f'Bearer {test_imeicheck}',
            'Content-Type': 'application/json'
        }
    else:
        payload = {
            'deviceId': imei,
            'serviceId': serviceId_live
        }

        headers = {
            'Authorization': f'Bearer {live_imeicheck}',
            'Content-Type': 'application/json'
        }

    response = requests.request('POST', url, headers=headers, json=payload)

    if response.status_code == 201:
        try:
            data = response.json()
            if 'resultUrl' in data:
                result_url = data['resultUrl']
                result_response = requests.get(result_url, headers=headers)  # Запрос на получение данных созданного запроса
                if result_response.status_code == 200:
                    formatted_result = format_json_response(result_response.text)
                    return formatted_result
                else:
                    return f'HTTP error: {result_response.status_code}'

            formatted_result = format_json_response(json.dumps(data))
            return formatted_result
        except json.JSONDecodeError:
            return 'error: Неверный JSON ответ'
    if response.status_code == 402:
        return 'Лимит запросов исчерпан'
    else:
        return f'HTTP error: {response.status_code}'


def validator_imei(imei: str) -> bool:
    """ Проверяет корректность imei
        0. IMEI имеет 15 знаков
        1. Убрать последнюю цифру - она проверочная
        2. Удвоить каждую вторую цифру, исключая проверочную
        3. Разбить все числа на цифры 17 -> 1 7
        4. Сложить все цифры и увеличить полученное число до следующего кратного 10
        5. Вычесть из полученного числа сумму цифр без проверочной цифры
        6. Если результат равен проверочному, то imei действителен
    """

    if len(imei) != 15 and imei.isdigit():
        return False
    else:
        # 1
        imei_without_check = imei[:-1]
        check_num = int(imei[-1])
        # 2
        new_imei = [int(digit) * 2 if i % 2 != 0 else int(digit) for i, digit in enumerate(imei_without_check)]
        # 3
        imei = [int(digit) for num in new_imei for digit in str(num)]
        # 4
        sum_ = sum(imei)
        # 5
        sum_10 = (sum_ + 9) // 10 * 10
        return sum_10 - sum_ == check_num
