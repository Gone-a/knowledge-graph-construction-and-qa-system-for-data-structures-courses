from flask import Flask,request,jsonify
from flask_cors import CORS
from query_fixed import DSAGraphQAFixed
app = Flask(__name__)
# CORS(app, origins=["http://localhost:8080"])

@app.route("/test",methods=["POST","GET"])
def test():
    msg="我需要帮助"
    reply_msg=reply(msg)

    return reply_msg
    Js=request.get_json()
    
    #Js["message"] 即为传入的字符串

    msg=Js["message"]
    # Js["message"]=reply(msg)
    # Js["img_src"]=get_img_src()
    Js["message"]+="H"
    Js["img_src"]="../assets/test.png"
    return_Js={"message":Js["message"],"img_src":Js["img_src"]}
    return jsonify(return_Js)

def reply(msg):
    #msg 为用户在前端输入的字符串
    #需要返回在前端显示的字符串。
    pass

def get_img_src():
    #得到图片的src以便于在前端上显示
    pass

app.run(host="localhost",port=5000)