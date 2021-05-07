import json
import numpy as np
f = open('./exchangeinfo.json',)
data = json.load(f)
f.close()

symbols = data["symbols"]
lotSizeDict = {}
for item in symbols:
  filters = item.get("filters")
  lotsize = 0
  for fil in filters:
    if fil.get("filterType") == "LOT_SIZE":
      minQty = fil.get("minQty")
      if "0." in minQty:
        cutTail = np.format_float_positional(float(minQty))
        lotsize = len(cutTail) - 2
  lotSizeDict[item.get("symbol")] = lotsize


f = open("lotsize.json","w")
f.write(json.dumps(lotSizeDict))
f.close()
