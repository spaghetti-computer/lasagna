import json,subprocess,sys
def q(kw):
    r=subprocess.run(["curl","-s","-m","20","-X","POST","-H","Content-Type: application/json","-A","Mozilla/5.0","https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList","-d",json.dumps({"keyword":kw,"currentPage":1,"pageSize":30})],capture_output=True,text=True).stdout
    return json.loads(r)["data"]["componentPageInfo"]["list"] or []
if __name__=="__main__":
    for c in sys.argv[1:]:
        L=[x for x in q(c) if x.get("componentCode")==c]
        if not L: print(c,"NOTFOUND"); continue
        x=L[0]; print(c,x["componentLibraryType"],x.get("componentPrices",[{}])[0].get("productPrice"),"stock",x["stockCount"],"min",x.get("leastPatchNumber"),x.get("erpComponentName"),x.get("componentModelEn"))
