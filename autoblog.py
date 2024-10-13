import requests
import json
import os
import openai
from PIL import Image
from bs4 import BeautifulSoup
from googleapiclient.discovery import build
import pprint
import pandas as pd
import random
import logging
import datetime
from dotenv import load_dotenv


# 環境変数から必要な設定情報を読み込みます
load_dotenv()
# 環境変数に含めるべきキーのリスト：
# - RAKUTEN_APP_ID: 楽天市場APIのアプリケーションID。楽天APIにアクセスするために必要。
# - LOG_DIR: ログファイルを保存するディレクトリのパス。ログを管理するために必要。
# - IMAGE_SAVE_PATH: ダウンロードした商品画像を保存するディレクトリのパス。
# - IMAGE_UPLOAD_URL: 画像をアップロードするWordPressのAPIエンドポイント。
# - WORDPRESS_USER: WordPressのユーザー名。API認証で使用。
# - AUTH_PASS: WordPressの認証パスワード。API認証で使用。
# - AZURE_URL: Azure OpenAI APIのエンドポイントURL。テキスト生成などで使用。
# - AZURE_API_KEY: Azure OpenAI APIのAPIキー。Azure APIリクエストの認証に必要。
# - SEARCH_API_KEY: Google Custom Search APIのAPIキー。口コミ検索で使用。
# - SEARCH_ENGINE_ID: Google Custom Search APIの検索エンジンID。
# - CATEGORY_ID: 投稿時に指定するWordPressのカテゴリID。
# - END_POINT_URL: WordPress REST APIのエンドポイントURL。ブログ記事を投稿する際に使用。


# 現在の日時を取得
current_time = datetime.datetime.now()

# 環境変数からログディレクトリを取得
log_dir = os.getenv('LOG_DIR')

# ファイル名に現在の日時を追加
log_file_name = current_time.strftime("%Y%m%d%H%M") + "app.log"

# ログファイルの完全なパスを設定
log_file_path = os.path.join(log_dir, log_file_name)

# ロガーの設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# ファイルハンドラーの設定
file_handler = logging.FileHandler(log_file_path)
logger.addHandler(file_handler)

# コンソールハンドラーの設定
console_handler = logging.StreamHandler()
logger.addHandler(console_handler)



# ログの記録
logger.info('このメッセージがログファイルに記録され、ターミナルにも出力されます')


# 指定されたURLから画像をダウンロードし、指定のパスに保存する関数
def download_image(url, save_path):
    response = requests.get(url)
    if response.status_code == 200:
        with open(save_path, 'wb') as file:
            file.write(response.content)
        logger.info('画像のダウンロードが完了しました。')
    else:
        logger.info('画像のダウンロードに失敗しました。')



REQUEST_URL ="https://app.rakuten.co.jp/services/api/IchibaGenre/Search/20140222"

# .envファイルからAPP_IDを取得
APP_ID = os.getenv('RAKUTEN_APP_ID')

# ジャンルID＝０とすると、ルートジャンル一覧を取得できる
params = {
    "applicationId" : APP_ID,
    "format": "json",
    "genreId" : "0",
}

res = requests.get(REQUEST_URL,params)
logger.info(res.status_code)

result = res.json()
#親ジャンル
logger.info(result)

# 各childからgenreIdを取得
genre_ids = [child['child']['genreId'] for child in result['children']]

# ランダムに一つのgenreIdを選択
genreid = random.choice(genre_ids)

# 結果を出力
logger.info("ランダムに選択された親ジャンルID↓")
logger.info(genreid)

# 親ジャンルIDに紐づく、子ジャンル一覧を取得できる
params = {
    "applicationId" : APP_ID,
    "format": "json",
    "genreId" : genreid,
}

res = requests.get(REQUEST_URL,params)
logger.info(res.status_code)

result = res.json()
logger.info("子ジャンルIDたち↓")
logger.info(result)

# 各childからgenreIdを取得
genre_ids = [child['child']['genreId'] for child in result['children']]

# ランダムに一つのgenreIdを選択
genreid2 = random.choice(genre_ids)

# 結果を出力
logger.info("ランダムに選択された子ジャンルID↓")
logger.info(genreid2)

## genreidに紐づく商品検索

REQUEST_URL ="https://app.rakuten.co.jp/services/api/IchibaItem/Search/20220601"


params = {
    "applicationId" : APP_ID,
    "format": "json",
    "genreId" : genreid2,
    "affiliateId" : "36e872cf.4472af68.36e872d0.1227316c",
}

res = requests.get(REQUEST_URL,params)
logger.info(res.status_code)
result = res.json()

logger.info("商品検索結果↓")
logger.info(result)

logger.info(len(result))

#10個結果が表示されるので、そこからランダムに１つ要素を抜き出そう

random_item = random.choice(result["Items"])
logger.info("ランダムに抽出した商品１つ↓")
logger.info(random_item)

# affiliateUrlキーの値を変数affiliateurlに格納
affiliateurl = random_item['Item']['affiliateUrl']
logger.info("アフィリエイトリンク↓")
logger.info(affiliateurl)

# itemNameキーの値を変数itemnameに格納
itemname = random_item['Item']['itemName']
logger.info("商品名")
logger.info(itemname)

# itemPriceキーの値を変数itempriceに格納
price = random_item['Item']['itemPrice']
# 3桁毎のカンマを入れる処理
itemprice = "{:,}".format(price)
logger.info("価格")
logger.info(itemprice)

# mediumImageUrlsキーの値を変数imageurlに格納
imageurl = random_item['Item']['mediumImageUrls'][0]['imageUrl']
logger.info("画像URL")
logger.info(imageurl)

# .envファイルから画像保存パスを取得
save_path = os.getenv('IMAGE_SAVE_PATH')

# 画像をダウンロード
download_image(imageurl, save_path)

image = Image.open(save_path)

# .envファイルからURLを取得
image_upload_url = os.getenv('IMAGE_UPLOAD_URL')


headers = {
"Content-Disposition": 'attachment; filename="my_image.jpg"',
"Content-Type": "image/jpeg",
}

# wordpressログイン情報
WORDPRESS_USER = os.getenv('WORDPRESS_USER')
AUTH_PASS = os.getenv('AUTH_PASS')


# アイキャッチ画像用に128×128のサイズのままの画像を、wordpressにアップして画像IDを取得

with open(save_path, 'rb') as img:
    r = requests.post(image_upload_url, headers=headers, data=img, auth=(WORDPRESS_USER, AUTH_PASS))

image_response_data = r.json()
eye_image_id = image_response_data.get('id')


# 画像のサイズを変更
new_image = image.resize((256, 256))

# 変更後の画像を保存
new_image.save(save_path)

with open(save_path, 'rb') as img:
    r = requests.post(image_upload_url, headers=headers, data=img, auth=(WORDPRESS_USER, AUTH_PASS))

image_response_data = r.json()
image_id = image_response_data.get('id')
image_url = image_response_data.get('source_url')
logger.info(f"Response body: {r.text}") 


affiliateurl = f"""
<div style="border: 1px solid black; padding: 10px;">
    <div style="text-align: center;">
        <a href="{affiliateurl}">
            <img src="https://mitsuru-media2.com/wp-content/uploads/2024/08/rakuten2.png" alt="Rakuten Logo" style="max-width: 100%; height: auto; margin: 0 auto; display: block;" />
        </a>
    </div>
    <table style="width: 100%; table-layout: fixed;">
        <tr>
            <td style="width: 50%;">
                <a href="{affiliateurl}">
                    <img src="{image_url}" alt="{itemname}" style="max-width: 100%; height: auto; display: block; margin: 0 auto;" />
                </a>
            </td>
            <td style="vertical-align: middle;">
                <div style="text-align: left; padding: 0 10px;">
                    <a href="{affiliateurl}" style="font-weight: bold; font-size: 80%; color: black; text-decoration: none;">{itemname}</a><br>
                    <a href="{affiliateurl}" style="font-weight: bold; color: black; text-decoration: none;">{itemprice}円</a><br>
                    <a href="{affiliateurl}" style="font-weight: bold; text-decoration: underline; color: black;">購入はこちら</a>
                </div>
            </td>
        </tr>
    </table>
    <br>
</div>
"""




# .envファイルからURLとAPIキーを取得
azure_url = os.getenv('AZURE_URL')
azure_api_key = os.getenv('AZURE_API_KEY')


# ヘッダーの設定
azure_headers = {
    'Content-Type': 'application/json',
    'api-key': azure_api_key,
}

system_message = {"role": "system", "content": "あなたはテキストを入力とし受け取り、そのテキストから商品名を抽出します。出力形式は以下の例を参考にしてください。(例1)入力:三河一色産 備長炭手焼き 昭和9年創業 魚しげのこだわりのひつまぶし 1名様お食事券、出力:魚しげのこだわりのひつまぶし 1名様お食事券 (例2)入力：春摘み苺アイス [ギフト箱30個入り] はしっこシャリシャリ 【楽ギフ_のし】、出力:はしっこシャリシャリ "}
user_message =  {"role": "user", "content":itemname}
messages = [system_message]  + [user_message]

azure_data = {
    "messages": messages,
    "temperature": 2.0,
    "max_tokens": 4096,
    "top_p": 0.95,
    "frequency_penalty": 0,
    "presence_penalty": 0,
    "stop": None
}

# リクエストを送信し、レスポンスを取得する
response = requests.post(azure_url, headers=azure_headers, data=json.dumps(azure_data))

if response.status_code in [200, 201]:
    itemname = response.json()['choices'][0]['message']['content']
else:
    logger.info("Error: ")
    logger.info(response.status_code)
    logger.info("Response body: ")
    logger.info(response.text) 

# AIによって抽出された商品名
logger.info("AIによって抽出された商品名を表示")
logger.info(itemname)


# .envファイルからAPIキーと検索エンジンIDを取得
api_key = os.getenv('SEARCH_API_KEY')
search_engine_id = os.getenv('SEARCH_ENGINE_ID')

# 「商品名 感想」をキーワードにしてgoogle検索
query = f"{itemname} 感想"
query2 = f"{itemname} 感想"

logger.info("検索エンジンへのクエリ")
logger.info(query)

# google検索結果で表示されるサイトのうち、スクレイピング（HTML解析）をするサイト数
site_num = 1

# Google Custom Search API を使って検索

service = build("customsearch", "v1", developerKey=api_key)
res = service.cse().list(q=query, cx=search_engine_id,num=site_num).execute()

# 検索結果を表示
logger.info("検索結果を表示")
logger.info(res)

summaries = []

for item in res['items']:
    url = item['link']
    
    # URLにアクセスして内容を取得
    response = requests.get(url)
    
    # BeautifulSoupでHTMLを解析
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # テキスト情報を取得
    text = soup.get_text()

    logger.info(f"URL({url})へアクセスして取得したテキスト情報：")
    logger.info(text)
    
    system_message = {"role": "system", "content": f"あなたはSEOに詳しいブロガーです。テキストを受け取り、そのテキストから「{query2}」に関する記事を作成するために必要となる情報を抽出し、箇条書きにしてください。箇条書きに含まれる内容は、抽象的な情報ではなく、より具体的な情報としてください"}
    user_message =  {"role": "user", "content":text}
    messages = [system_message]  + [user_message]

    # ヘッダーの設定
    azure_headers = {
        'Content-Type': 'application/json',
        'api-key': azure_api_key,
    }

    # リクエストデータの作成
    azure_data = {
        "messages": messages,
        "temperature": 2.0,
        "max_tokens": 4096,
        "top_p": 0.95,
        "frequency_penalty": 0,
        "presence_penalty": 0,
        "stop": None
    }

    # リクエストを送信し、レスポンスを取得する
    response = requests.post(azure_url, headers=azure_headers, data=json.dumps(azure_data))
    
    if response.status_code in [200, 201]:
        summary = response.json()['choices'][0]['message']['content']
        summaries.append(summary)
    else:
        logger.info("Error: ")
        logger.info(response.status_code)
        logger.info("Response body: ")
        logger.info(response.text)        

for idx, s in enumerate(summaries):
    logger.info(f"要約文 {idx + 1}：")
    logger.info(s)    

# summariesリストの中身を結合
joined_summaries = ' '.join(summaries)

# 結合したテキストデータを出力
logger.info("結合されたテキスト： ")
logger.info(joined_summaries)


# AIにh本文を作成してもらう(GPT4)
messages = [
    { "role": "system", "content": f"あなたはSEOに詳しいブロガーです。テキストを受け取り、そのテキストとあなたが保有している情報から「{query}」に関するブログ記事を作成します。バズるような記事を作成してください。あなたがその商品を使った感想を述べているような文章にしてください。あなたからの回答(content)はそのままwordpressブログの本文に使われます。可能な限り長い記事を作成してください。見出しもつけるなどしてSEO対策もしてください。強調すべき箇所は太文字・下線をして強調してください。必ずhtml形式で返信してください。<h1>タグは使用しないでください。返信は、必ず<h2>から始めてください。以下は返信例になります。<h2>1. 楽天カード</h2><p>楽天カードは、楽天市場での買い物や楽天トラベルでのホテル、旅行パックの予約でポイントがたくさん貯まります。さらに、今なら新規入会で最大5,000ポイントもらえるキャンペーンを実施中です。</p>" },
    { "role": "user", "content": joined_summaries },
]

logger.info(messages)




# リクエストデータの作成(GTP4)
# .envファイルからURLとAPIキーを取得
azure_url2 = os.getenv('AZURE_URL2')
azure_api_key2 = os.getenv('AZURE_API_KEY2')


# ヘッダーの設定
azure_headers2 = {
    'Content-Type': 'application/json',
    'api-key': azure_api_key2,
}


azure_data2 = {
    "messages": messages,
    "temperature": 2.0,
    "max_tokens": 4096,
    "top_p": 0.95,
    "frequency_penalty": 0,
    "presence_penalty": 0,
    "stop": None
}
# リクエストを送信し、レスポンスを取得する
response = requests.post(azure_url2, headers=azure_headers2, data=json.dumps(azure_data2))


# レスポンスを解析し、内容を取得する
if response.status_code in [200, 201]:
    content = response.json()['choices'][0]['message']['content']
else:
    logger.info("Error: " )
    logger.info( response.status_code)    
    logger.info("Response body: ")
    logger.info(response.text)
    exit()  # OpenAIへのリクエストが失敗した場合、プログラムを終了する

# responseからmessage全体を取り出す
message = response.json()['choices'][0]['message']

logger.info(content)

##　記事件名作成
messages = [
    { "role": "system", "content": "あなたはSEOに詳しいブロガーです。あなたはブログ本文を受け取り、そのブログ本文に適したブログ件名を１つ作成します。あなたからの回答は、そのままwordpressブログの件名に使われます。３０文字以内で件名を考えてください。" },
    { "role": "user", "content": content},
]

# リクエストデータの作成
azure_data = {
    "messages": messages,
    "temperature": 2.0,
    "max_tokens": 4096,
    "top_p": 0.95,
    "frequency_penalty": 0,
    "presence_penalty": 0,
    "stop": None
}

# リクエストを送信し、レスポンスを取得する
response = requests.post(azure_url, headers=azure_headers, data=json.dumps(azure_data))

# レスポンスを解析し、内容を取得する
if response.status_code in [200, 201]:
    title_prompt = response.json()['choices'][0]['message']['content']
else:
    logger.info("Error: " )
    logger.info( response.status_code)    
    logger.info("Response body: ")
    logger.info(response.text)
    exit()  # OpenAIへのリクエストが失敗した場合、プログラムを終了する

# responseからmessage全体を取り出す
message = response.json()['choices'][0]['message']

logger.info("件名:")
logger.info(title_prompt)


affiliate_link = affiliateurl

# # 最初の<h2>タグを見つけて、その直前にアフィリエイトリンクを挿入
first_h2_index = content.find('<h2>')
# アフェリエイトリンク３つを横に並べるために、「styled_affiliate_link」を定義。これをしないと縦に並んでしまう。
styled_affiliate_link = f'<div style="display: inline-block; margin-right: 10px;">{affiliate_link}</div>'

if first_h2_index != -1:
    content = content[:first_h2_index] + styled_affiliate_link + content[first_h2_index:]

# コンテンツの最後にアフィリエイトリンクを追加
content += styled_affiliate_link


# 投稿するURLの設定
END_POINT_URL = os.getenv('END_POINT_URL')



# 投稿内容
p_title = title_prompt # AIからのレスポンスをブログの件名とする
p_content = content   # AIからのレスポンスをブログの本文とする
p_status = "publish"
p_featured_media = eye_image_id  # アイキャッチ画像のメディアID

# カテゴリのIDを指定
p_categorie = [int(os.getenv('CATEGORY_ID'))]


payload = {
    'title': p_title,
    'content' : p_content ,
    'status' : p_status,
    'slug' : 'human',    
    'featured_media': p_featured_media,
    'categories': p_categorie
}

headers = {'content-type': "Application/json"}

# WordPress REST APIに投稿する
r = requests.post(END_POINT_URL, data=json.dumps(payload), headers=headers, auth=(WORDPRESS_USER, AUTH_PASS))
logger.info(r)
response_data = r.json()
post_id = response_data.get('id')

GET_POST_URL = f"{END_POINT_URL}/{post_id}"
r = requests.get(GET_POST_URL, auth=(WORDPRESS_USER, AUTH_PASS))
existing_post_data = r.json()
existing_content = existing_post_data.get('content', {}).get('rendered', '')

logger.info("existing_content↓")
logger.info(existing_content)