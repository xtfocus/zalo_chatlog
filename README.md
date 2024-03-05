# Zalo Chatlog: Execution idea

## Overview

This is the **proof-of-concept** repo of Zalo Chatlog feature extraction pipelines:

* preprocessing pipeline: removing errorneous rows, recognize automated and typed response
* separation pipeline: different transformation techniques for fully automated/typed conversations vs others

## Some Business domain knowledge

Each message can come from:

* robot
* human agent
* user (the customer)

Each message can be categorized further as follows:

```
|--- robot
|    |---- request_human_support
|    |    |---- success
|    |    |---- failure
|    |
|    |---- text
|    |    |---- greeting (e.g., "Dạ em chào Anh/Chị, em có thể hỗ trợ gì cho mình ạ...")
|    |    |---- ask_phone_general (e.g., "Anh, chị vui lòng nhắn tin SỐ ĐIỆN THOẠI MUA HÀNG để KÍCH HOẠT ...")
|    |    |---- closing_time (e.g., "Nhà thuốc Long châu đã nhận được yêu cầu hỗ trợ từ Quý khách, nhưng rất tiếc...")
|    |    |---- hist_vax_empty (e.g., "Tiếc quá! Nhà mình chưa tiêm chủng tại Long Châu nên chưa có thông tin...")
|    |    |---- next_vax_empty (e.g., "Nhà mình hiện Chưa Có Lịch Hẹn Tiêm Chủng tiếp theo")
|    |    |----  menu_vax (e.g., "Anh/Chị vui lòng chọn thông tin cần tra cứu bên dưới:
|    |                                                    Lịch sử tiêm chủng
|    |                                                    Lịch tiêm tiếp theo")
|    |---- image
|         |---- ask_phone_vax (e.g., "Vaccine/NhapSDT.png")
|         |---- song_khoe (e.g., "CHĂM CHỈ TẬP LUYỆN")
|         |---- recommendation (e.g., "xem thêm sản phẩm", "Xem ngay sản phẩm" )
|         |---- his_vax (e.g., "Vaccine/LichSuTiemChung")
|         |---- vax_reminder (e.g., "SapDenLichHenTiemChung" )
|         |---- diem_hien_tai (e.g., "Banner/DacQuyen", "để đổi quà nhé ạ")
|         |---- ask_phone_bat_dau_tich_diem (e.g., "Banner/HDNhapSDT")
|         |---- moi_doi_diem (e.g.,"khuyen-mai/dquyen", "mời nhà mình", "0D.png", "QUÀ")
|         |---- moi_quan_tam (e.g., "PleaseFollow.jpg")
|         |---- dua_ma_qr (e.g., "Mình vui lòng đưa mã QR")
|
|--- human agent
|    |---- file (screenshots, etc.)
|    |---- text 
|         |---- confirm_order (e.g., "Người đặt ... Địa chỉ khách hàng...") 
|         |---- other text (depends on the actual conversation)
|
|--- user
     |---- payload (pressing buttons)
     |    |---- welcome_flow            
     |    |---- Diemcuatoi              
     |    |---- Muathuoc                
     |    |---- goodbye_unfollow        
     |    |---- Tiemchung               
     |    |---- MaQR                    
     |    |---- Lịch sử tiêm chủng      
     |    |---- Gui_diem                
     |    |---- Lịch hẹn tiêm tiếp theo 
     |    |---- gui_qrcode_khachhang    
     |    |---- Point_log               
     |    |---- etc.
     |
     |---- file (screenshots, etc)
     |---- sticker (zalo sticke)
     |---- user_send_location 
     |---- text
          |---- phone number
          |---- other text (depends on the actual conversation)
```



## How to install dependencies

```
pip install -r src/requirements.txt
```

## How to run your Kedro pipeline

Create directory `data/01_raw` 

Rename your daily parquet to `chatlog.parquet`, copy it to `data/01_raw`

It should look like this

```
<PROJECT DIR>
├── conf
│   ├── base
│   │   ├── catalog.yml
│   │   ├── logging.yml
│   │   ├── parameters_data_preprocessing.yml
│   │   ├── parameters_data_refinement.yml
│   │   └── parameters.yml
│   ├── local
│   │   └── credentials.yml
│   └── README.md
├── data
    ├── 01_raw
        ├── chatlog.parquet # Raw chatlog df
```

You can run your whole Kedro project with:

```
kedro run
```

To run FROM a node:
```
kedro run --from-nodes intent.organic.messages
```

(Replace `intent.organic.messages` with your actual node)

To run only one node:

```
kedro run --nodes intent.organic.messages
```

## To extract the refined message + conversation code(for annotation task)
```
kedro run  --to-nodes refined.organic.messages
```

### Install the LLM model

You need the `mistral:lastest` model
```
ollama pull mistral
```

Once the download finishes, initialize the local server with
```
ollama serve
```

Starts playing with the model. For batch inference using kedro:

```
kedro run --nodes intent.organic.messages
```
