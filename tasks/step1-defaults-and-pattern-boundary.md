# 第 1、2 項實作計畫 —— Step 1 預設值與 MVC／MVVM 分界

依據：使用者 2026-09-01 的裁示。實作前請先確認本計畫，特別是第五節的三個未決點。

---

## 一、裁示原文要點

**第 1 項（Step 1 沒有備案）**

* 缺乏資訊 → 問使用者要哪一個 pattern。
* 問不到又缺乏資訊 → **預設 MVC**。

**第 2 項（模式與資料分界）**

* MVC：一定會 `apply` 一個 Composer。
* MVVM：設定 `viewModel` 屬性，並使用 data binding 語法。
* 兩者都是 Controller，控制**所套用的那個元件及其旗下所有子元件**。
* 不排除使用者自己混用，但 **zul-writer 產生內容時一次只用一種，不混用**。
* Model-driven 時，資料元件（grid／listbox／tree 等）的 model 來源：MVC 來自 Composer，MVVM 來自 ViewModel。
* 靜態資料直接寫在 ZUL：grid 用 `row`、listbox 用 `listitem`、tree 用 `treeitem`。

---

## 二、第 1 項 —— Step 1 逐題預設值

改 `skills/zul-writer/SKILL.md` 的 Step 1（第 84–142 行）。目前七題**全部沒有預設值**，
六次跑動全數撞上，每次都自行發明「抄專案既有慣例」這個技能從未認可的作法。

| # | 問題 | 問得到時 | 問不到時的預設 | 依據 |
|---|---|---|---|---|
| 1 | ZK 版本 | 先從 `pom.xml`／`ivy.xml`／`build.gradle` 偵測 | **10.x** | 不是新決定，是對齊既有事實：`validate-zul.py` 已經 `default="10"`，`preview-zul.py` 已經 `DEFAULT_ZK_VERSION = "10.2.1"`。技能講一套、工具做另一套，正是第 5 項那種不一致的來源 |
| 2 | 頁面用途 | 問 | **不設預設，從請求本身讀** | 使用者一定描述了要什麼頁；這題沒有猜的空間，硬給預設反而會蓋掉已經講明的需求 |
| 3 | MVC / MVVM | 問 | **MVC** | 使用者裁示 |
| 4 | 靜態 / Model-driven | 問 | **靜態（literal）** | 與既有的兩段式規則一致：新頁面本來就先寫 literal。只有在請求指名了真實資料來源時才走 model-driven |
| 5 | 版面 | 問 | **不設預設，由第 2 題的用途推導**，並寫出推導理由 | 版面是設計稿或請求裡最具體的部分；給一個固定預設等於忽略它 |
| 6 | ZK Charts | 只在需要圖表時問 | 不適用 | — |
| 7 | 主題／資料密度 | 高密度時建議 `iceblue_c` | **維持預設主題**，並在回報裡說明可換 | 換主題會改變整頁外觀，不該在沒人確認時發生 |

另加一條貫穿規則：**任何一題用了預設值，都要在最後回報裡點名「這題沒問到，我用了 X」。**
預設值的價值在於可預測且可覆核，沉默的預設值兩者皆失。

**「抄專案既有慣例」怎麼處理 → 見第五節 D16。**

---

## 三、第 2 項 —— 三個子問題，裁示回答了兩個半

### (a) 模式分界 —— 已有明確答案

寫進 Step 1 第 3 題與 Step 2，把裁示的判準原樣講清楚：

* **MVC** = 某個元件上有 `apply="com.foo.MyComposer"`。
* **MVVM** = 某個元件上有 `viewModel="@id('vm') @init('com.foo.MyVM')"`，並使用 `@load`／`@bind`／`@command` 繫結語法。
* 兩者都是 Controller，**作用範圍是被套用的那個元件及其所有子元件**。
* **一頁只出一種。** ZK 允許混用，但 zul-writer 不產生混用的頁面 —— 混用的頁面沒有單一的
  「資料從哪來」答案，第 5 步自審與抽取階段都會失去依據。

### (b) 資料與版面文字的分界 —— 裁示沒直接回答，以下是擬案

四次跑動各自劃線，三次明確標記為判斷題。擬定的規則：

> **會隨資料而變的字是資料；不論資料如何都固定的字是版面文字。**
>
> * 版面文字（留在 ZUL）：欄位標題、按鈕文字、區塊標題、單位、空狀態訊息、驗證提示。
> * 資料（model-driven 時搬進 controller）：儲存格值、清單項目、筆數、金額、狀態標籤。

這條規則是我提的，不是裁示的。**若你有不同劃法請直接推翻**，否則我按此寫入。

### (c) 兩段式規則的 MVC 版本 —— 裁示提供了缺的那一半

現行〈Model-driven pages: write the data in, then take it out〉（第 188–210 行）整節是
`@load(vm.…)` 與 bound `model`，**沒有 MVC 版本**。要補的內容：

* **第一輪（literal）**：資料寫成 literal 子元素 —— grid 用 `<row>`、listbox 用 `<listitem>`、
  tree 用 `<treeitem>`。MVC 的第一輪其實比 MVVM 乾淨：沒有 `@load`，就沒有 dimmed 佔位文字，
  截圖直接就是使用者會拿到的頁面。
* **抽取**：literal 搬進 Composer 成為 model，ZUL 端**刪掉那些 literal 子元素**，
  改由 `setModel()` 供應。搬的是值，不是結構。
* **關鍵一句（新增）**：**literal 子元素與 model 不可併存。** 這正是 R3 軼事
  ——「`Listbox.setModel()` 與寫死的 `<listitem>` 併存並不安全」—— 而 R3 是靠鄰近警告
  **類比推得**的，技能裡從來沒寫。裁示的「靜態寫 ZUL／model-driven 來自 controller」
  正好讓這條變成一句必然的推論，而不是一條要背的例外。
* 抽取後用 `--run-controllers` 重渲染確認版面沒有位移。

### (d) 沒有 literal 路徑的元件 —— 裁示未涵蓋 → 見第五節 D17

裁示的靜態寫法列了 grid／listbox／tree。`<charts>` 在 ZUL 裡**沒有任何寫死資料的方法**，
所以「先寫 literal 再抽取」對它根本跑不起來。R1 就是撞在這裡。

---

## 四、可機械化的部分

第 (c) 點的「literal 與 model 不可併存」有一半可以被驗證器抓到：

* **看得到**：ZUL 端同時出現 `model="@load(...)"` 與 literal `<listitem>`／`<row>`／`<treeitem>`
  子元素 —— 純 ZUL 訊號，`validate-zul.py` Layer 3 抓得到。
* **看不到**：MVC 的 `setModel()` 寫在 Java 裡，ZUL 端只看得到 literal 子元素，
  validate-zul.py 沒有理由懷疑它。**這一半只能靠散文。**

→ 這條規則要不要寫成程式碼，見第五節 D18。

---

## 五、未決點

**裁示（2026-09-01）：D16 = B，D17 = A。D18 待議，見下方實測。**

### D16：專案既有慣例還算不算數？ ✅ 已決：選項 B（2026-09-01 已實作）

**實作。** `skills/zul-writer/scripts/detect-pattern.py`，`test/run-pattern-tests.py` 七項全過。
一面倒的判準定為**另一側為零**，不是任何比例門檻 —— 6 比 2 仍然是 `mixed`。理由：任何百分比
都是憑空發明的數字，而混合的專案本來就回到 MVC，差別只在報告說的是「這專案是 MVC」還是
「這專案混用，我用了預設」。後者才是實話。多加的一個特例是
`apply="org.zkoss.bind.BindComposer"` 判為 MVVM —— 那是 MVVM 自己的 binder，
判成 MVC 會讓結論完全相反（本 repo 的 `test/valid/zk-5696.zul` 正是這個寫法）。


**背景。** 裁示是「缺資訊→問；問不到→MVC」。六次跑動全都自行發明了第三條路：抄專案既有頁面。
本 repo 現在 `apply=` 6 個檔、`viewModel=` 2 個檔 —— R4 抄到 MVC，R6 看到不一致就改用自己的推理。

**影響。** 這決定第九節那支「模式偵測腳本」要不要做。

* **【選項 A】預設值是絕對的（建議）**：問不到就用 MVC，不看專案。｜**代價：** 一個全 MVVM 的專案會被加進一頁 MVC。腳本不用做。
* **【選項 B】專案一面倒時可覆蓋預設**：`apply=` 與 `viewModel=` 只數 ZUL 側（Java 側的 `@Init` 會說謊 —— 本 repo 數到 0 卻有兩個 ViewModel），一面倒就跟，混合就回到 MVC 並說明。｜**代價：** 一支小腳本 ＋ Step 1 多一段散文。

### D17：`<charts>` 這種沒有 literal 路徑的元件，第一輪怎麼辦？ ✅ 已決：選項 A

**背景。** 圖表無法寫死在 ZUL，兩段式規則的第一輪對它不存在。

* **【選項 A】圖表區塊豁免（建議）**：其餘部分照走 literal 第一輪；圖表從一開始就寫 controller，
  並在該輪用 `--run-controllers` 判讀。｜**代價：** 該頁的第一輪需要 controller 能編譯，
  而 R1 正好撞過「`.class` 陳舊、`mvn -o compile` 不重編」。
* **【選項 B】先放等尺寸佔位框**：第一輪用一個固定高寬的空容器佔位，版面定案後才換成真圖表。
  ｜**代價：** 佔位框與真圖表的高度若不同，版面要重判一次。

### D18：「literal 與 model 併存」要寫成驗證規則嗎？ ✅ 已決：選項 C（`preview-zul.py`，兩側都覆蓋）

**實測（2026-09-01）。** 四種配置各渲染一次，全部 `STATUS: ok`、零警告：

| 配置 | 結果 |
|---|---|
| MVVM listbox：`model="@load(vm.items)"` ＋ literal `<listitem>` | literal **消失**，10 筆 model 資料照常顯示 |
| MVC listbox：literal `<listitem>` ＋ composer `setModel(10 筆)` | literal **消失** |
| MVC listbox：literal `<listitem>` ＋ composer `setModel(空 list)` | literal **消失**，整張列表空白 |
| MVVM grid：`model="@load(vm.items)"` ＋ literal `<row>` | literal **消失** |

**model 一律吃掉 literal 子元素，連空 model 都吃，而且不出任何聲音。**

**這改變了問題的性質。** R3 記的是「併存並不安全」，聽起來像會炸。實際上更麻煩：
**它安靜且看起來正確**。頁面渲染得完全正確，所以第 5 步「看圖」在結構上不可能抓到它；
留在 ZUL 裡的那個 literal 宣稱要顯示一筆它從來沒顯示過的資料，下一個去改那一行的人
會發現怎麼改都沒反應。**這和圖示缺陷是同一類：渲染看不見的缺陷。** 那正是 LAYOUT 規則
存在的理由，所以我把建議從 A 改成 B。

* **【選項 A】只寫散文**：不動任何腳本。｜**代價：** 唯一能抓到它的機制放棄不用。
* **【選項 B】散文 ＋ `validate-zul.py` Layer 3 規則（建議）**：抓 ZUL 端同時出現
  `model="@load(...)"` 與 literal `<listitem>`／`<row>`／`<treeitem>`。｜**代價：** 一條規則 ＋ 測試；
  MVC 側（`setModel()` 在 Java 裡）仍然抓不到。
* **【選項 C】改由 `preview-zul.py` 抓，兩側都能覆蓋**：`--run-controllers` 同時握有 ZUL 原始碼
  與渲染後的 DOM，所以「ZUL 寫了 literal 但 DOM 裡找不到那段文字」這個訊號**不在乎
  `setModel()` 寫在哪裡**，MVC 側也抓得到。｜**代價：** 分頁（paging）或虛擬捲動的 listbox
  本來就不會把所有列渲染出來，上線前必須先確認偽陽性率 —— 這是三個選項裡唯一需要先做實驗的。

---

## 六、驗證方式

1. 改完 `SKILL.md` 後對七題逐題 grep，確認每題都有預設值或明寫「不設預設，理由是 X」。
2. 用本 repo 的 showcase 頁面反向核對第 (a) 點的判準：每一個 `.zul` 都要能被這條判準
   唯一地歸類成 MVC 或 MVVM，歸不進去的就是判準有洞。
3. 第 (c) 點的 MVC 兩段式，拿一個實際的 listbox 頁面走一遍：literal 第一輪 → 抽取 →
   `--run-controllers` 重渲染，確認版面沒位移、且 ZUL 裡不再有 literal 子元素。
4. `test/run-preview-tests.py` 全套仍需全過。

**實作後的驗證結果（2026-09-01）：**

| 項 | 結果 |
|---|---|
| 1. 七題逐題預設值 | ✅ 五題有預設、兩題明寫「不設預設」並附理由 |
| 2. 判準能唯一分類 | ✅ 全 repo 58 個 `.zul` 全部分類完成，無歸不進去的檔案 |
| 3. MVC 兩段式 | ✅ 由 `literal-rows-setmodel.zul` fixture 與 A25 釘住 |
| 4. 測試 | ✅ `run-preview-tests.py` 32/32、`run-pattern-tests.py` 7/7、`run-regression.py` 0 drift |

---

## 七、本輪未涵蓋

* **第 6 項（折疊元件狀態列舉）仍未裁示** —— 要列哪些元件還沒定，該項維持 🟡。
* **「至多兩輪修正」的上限仍未檢討** —— 從未被量測支持過。
* **`detect-pattern.py` 沒有送使用量 ping**（另兩支腳本有）—— 見下方 D19。

---

## 八、新的未決點

**裁示（2026-09-01）：D19 = A（不送），D20 = 維持 2.0.0。兩項都不需要改動程式碼。**

### 議題 D19：`detect-pattern.py` 要不要送使用量 ping？ ✅ 已決：選項 A（不送）

**背景狀況。** `validate-zul.py` 與 `preview-zul.py` 各自送一次匿名 ping。新腳本目前**不送**。

**影響與風險。** 這不是程式碼問題（約十行），是**指標定義**問題：目前一次技能跑動會送出
兩個事件，加了第三個發送端之後，同樣一次跑動變成三個事件，**版本交界處的趨勢線會斷掉**，
而且斷得看不出來 —— 數字會像是使用量上升了 50%。

* **【選項 A】不送（建議，現況）：** 這支腳本跑在同一次技能跑動裡，那次跑動已經由另外兩支
  回報過了。｜**代價：** 與「每支腳本都送 ping」的慣例不一致，未來維護者可能誤以為是漏寫
  （已在腳本 docstring 裡寫明理由）。
* **【選項 B】照慣例送：** 三支一致。｜**代價：** 需要決定舊資料怎麼處理 —— 是接受趨勢線
  斷點，還是在事件裡加欄位區分來源。

### 議題 D20：技能版本要不要往上跳？ ✅ 已決：維持 2.0.0

**背景狀況。** `0c5d705` 與 `4b917c0` 加了一條 `LAYOUT` 規則、一支新腳本、Step 1 一整節，
版號仍是 2.0.0。

**裁示：維持 2.0.0。** 分支尚未收斂，剩下的工作（兩輪上限、第 6 項）還會改到同一批檔案，
所以版號留到收斂時一次跳。**在那之前不要動三處版號中的任何一處** ——
`SKILL.md` 的 `metadata.version`、`marketplace.json`、兩支腳本的 `SKILL_VERSION`
必須一起改，改一處就是漂移。

`gemini-extension.json` 是另一條版本線，本來就不跟著跳，不算漂移。
