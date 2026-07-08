# FiveM MLO制作向け Sollumz + Sollumz Model Prepper ワークフロー

このドキュメントは、Blender / Sollumz を使って FiveM 向けMLOを作成する際に、**Sollumz Model Prepper** をどのタイミングで使うと安全かをまとめた補助ガイドです。

対象読者は、FiveM MLO制作の入門手順に沿って作業しながら、
「どこでチェックすればいいのか」  
「Materialをどう判断すればいいのか」  
「Export前に何を確認すればいいのか」  
で迷いやすい人です。

---

## 役割分担

### Sollumz Tool が担当すること

Sollumz Tool は、GTA V / FiveM 向けアセット制作の本体です。

主に以下を担当します。

```text
- Drawable / YDR 系の作成・変換
- Collision / YBN 系の作成
- YTYP / YMAP / Room / Portal 関連設定
- GTA V / CodeWalker XML形式へのExport
- Sollumz Material / Shader設定
```

### Sollumz Model Prepper が担当すること

Sollumz Model Prepper は、Sollumz Toolを置き換えるものではありません。  
**Export前の検査・分類・選択補助**を行うツールです。

主に以下を担当します。

```text
- Transform / Normal / Geometry / UV / Material のPreflight Check
- 問題ObjectのResult表示
- Zero Area Faces / Boundary Edges / Non-Manifold / Loose GeometryなどのReview選択
- Material AssistantによるMaterial分類
- Materialカテゴリ別・Material別のObject選択補助
```

Model Prepperは、Material変換やSollumz Exportを自動実行しません。  
実際の変換・設定・Exportは、必ずSollumz Tool側で行います。

---

# 推奨ワークフロー

## 1. ツールと素材を準備する

まず、Blender、Sollumz、CodeWalker、元になる建物モデルやテクスチャを準備します。

この段階では、Model Prepperはまだ必須ではありません。  
まずはBlenderにモデルを読み込み、編集できる状態にします。

---

## 2. モデルをBlenderへ導入する

建物や内装モデルをBlenderに読み込みます。

この時点で確認したいこと。

```text
- Objectが極端に大きすぎないか / 小さすぎないか
- 不要なObjectが混ざっていないか
- 建物、床、壁、天井、窓、ドアなどが作業しやすく分かれているか
- 編集対象と参照用Objectが混ざっていないか
```

まだSollumz変換に入る前なので、ここではModel PrepperのPreflightを軽く実行して、致命的な問題だけ早めに見つけます。

推奨操作:

```text
1. MLOに使うMesh Objectを選択
2. Sollumz Prepper パネルを開く
3. Run Preflight
4. ERROR / WARN を確認
```

この段階で見るべき主な項目:

```text
- Scale not applied
- Non-zero rotation
- Missing UV
- Loose geometry
- Zero area faces
```

---

## 3. インテリア形状を作成する

床、壁、天井などのインテリア形状を作ります。

この段階では、Model Prepperを「作業途中の健康診断」として使います。

おすすめタイミング:

```text
- 床・壁・天井を作ったあと
- 窓やドア用の穴を開けたあと
- BooleanやKnifeを使ったあと
- Objectを結合・分離したあと
```

Run Preflightで特に見る項目:

```text
Geometry:
- Zero Area Faces
- Open Boundary Edges
- Complex Non-Manifold Edges
- Loose Geometry
- Duplicate Vertices

Normal:
- Normal Flip Suspected

UV:
- Missing UV
- UV Out of Bounds
```

Open Boundary Edgesは、窓穴やドア穴などで意図的に出る場合があります。  
すべてがエラーではありません。  
Model Prepperでは、危険度の高いComplex Non-Manifoldと、確認が必要なOpen Boundaryを分けて見ます。

---

## 4. テクスチャを反映する

テクスチャ作業に入ったら、Material Assistantを使います。

ここは初心者が迷いやすいポイントです。

特に迷いやすいこと:

```text
- どのMaterialをNORMAL_SPECにすればいいのか
- 窓やガラスは通常Materialと同じでいいのか
- Cutout系のフェンスや葉っぱはどう扱うのか
- Convert All Materialsを押していいのか
- Material数が多いとき、どれから見るべきか
```

Model Prepperでは、この判断を補助するためにMaterial Assistantを使います。

操作:

```text
1. 対象Mesh Objectを選択
2. Material Assistant > Analyze Materials
3. Summaryを確認
4. カテゴリ別にSelect
5. 該当Objectを確認
6. Sollumz Tool側でMaterialを手動変換・設定
```

Material Assistantの分類:

```text
NORMAL_SPEC
- 通常の不透明Material候補
- 壁、床、天井、家具などのベースになりやすい

ALPHA
- 透明・半透明Material候補
- ガラス、窓、透明表示が必要そうなもの

CUTOUT
- 抜き表現が必要そうなMaterial候補
- フェンス、格子、葉、デカールなど

MISSING_TEXTURE
- Image Textureが見つからないMaterial
- 先にテクスチャ割り当てを確認する

MANUAL_REVIEW
- 自動判断が難しいMaterial
- 手動確認が必要
```

重要:

```text
Material Assistantの結果は「候補」です。
正解を保証するものではありません。
```

特に `ALPHA` / `CUTOUT` / `MANUAL_REVIEW` は、必ず実際の見た目と用途を確認してください。

やってはいけないこと:

```text
- Convert All Materialsを何も確認せず押す
- 透明Materialを全部NORMAL_SPECにする
- Missing Textureを放置してExportする
- Material Assistantの分類を絶対の正解として扱う
```

---

## 5. MaterialをSollumz Toolで手動設定する

Material Assistantで分類を確認したら、実際のMaterial変換はSollumz Toolで行います。

基本方針:

```text
NORMAL_SPEC候補:
- まず通常の不透明Materialとして確認
- 壁、床、天井、家具などに使いやすい

ALPHA候補:
- ガラスや透明Materialとして確認
- 表示順や透過の問題が出やすいので手動確認

CUTOUT候補:
- 抜き表現が必要なMaterialとして確認
- フェンス、格子、葉、デカールなどは特に注意

MISSING_TEXTURE:
- 変換前にImage Textureの割り当てを確認

MANUAL_REVIEW:
- 用途を見て個別判断
```

Model PrepperのSelectボタンを使うと、該当Materialを使っているObjectを選択できます。

```text
カテゴリSelect:
- NORMAL_SPEC候補を使うObjectをまとめて選択
- ALPHA候補を使うObjectをまとめて選択
- CUTOUT候補を使うObjectをまとめて選択

Material別Select:
- 個別Materialを使っているObjectだけを選択
```

これにより、Material数が多い場合でも「どのObjectが対象か」を確認しやすくなります。

---

## 6. 窓・ドア・Face設定を行う

窓やドアを作成したら、再度Preflightを実行します。

確認したい項目:

```text
- 窓やドア周辺に不要なZero Area Facesがないか
- ドア穴や窓穴のBoundaryが意図通りか
- Normalが裏返っていないか
- UVが欠落していないか
- Materialが未設定のObjectがないか
```

Review Toolsを使うと、問題箇所へ移動しやすくなります。

```text
Select Zero Area Faces
Select Open Boundary Edges
Select Complex Non-Manifold Edges
Select Loose Geometry
Select Duplicate Vertices
Select UV Out-of-Bounds Faces
```

注意:

```text
Review Toolsは選択補助です。
Meshを自動修正するものではありません。
```

---

## 7. Collisionを作成する

コリジョンはSollumz Tool側で作成・設定します。

Model Prepperはコリジョンを自動生成しません。  
ただし、Collision作成前の元Meshチェックには使えます。

確認ポイント:

```text
- 元Meshに不要なLoose Geometryがないか
- 極端に細かすぎる形状をそのままCollision化しようとしていないか
- Scaleが未適用でないか
- Complex Non-Manifoldが残っていないか
```

Collision用Objectは、見た目用Meshとは別に整理するのがおすすめです。

---

## 8. YTYP / Room / Portalを設定する

YTYP、Room、Portal関連はSollumz Tool側の作業です。

Model PrepperはRoomやPortalを自動作成しません。  
ただし、作業前にObject構成を整理する補助には使えます。

おすすめ:

```text
- MLO用Collectionを分ける
- Interior / Collision / Portal / Helper を整理する
- Export対象と非Export対象を分ける
- 不要Objectを非表示ではなく、作業用Collectionへ分離する
```

---

## 9. Export前の最終Preflight

Export直前に、必ずModel Prepperで最終チェックを行います。

操作:

```text
1. Export予定のMesh Objectを選択
2. Run Preflight
3. ERRORを優先して確認
4. WARNを用途に応じて確認
5. Material Assistantを再実行
6. Missing Texture / Manual Review が残っていないか確認
```

Export前に特に見たい項目:

```text
ERROR:
- Scale not applied
- Missing UV
- Complex Non-Manifold
- Missing Material

WARN:
- Normal Flip Suspected
- UV Out of Bounds
- Open Boundary Edges
- High Vertex Count
- Texture Non Power-of-Two
- Missing Texture
```

WARNは必ずしも失敗ではありません。  
たとえばUVタイリングや意図的な開口部はWARNとして出ることがあります。  
ただし、Export前には「意図したWARNか」を確認してください。

---

## 10. Sollumz ToolでExportする

PreflightとMaterial確認が終わったら、Sollumz ToolでExportします。

基本:

```text
1. Export対象Objectを選択
2. 非表示Objectが混ざっていないか確認
3. Sollumz ToolからExport
4. XMLをCodeWalker側で変換・確認
```

---

## 11. CodeWalkerで確認する

CodeWalkerで読み込み、以下を確認します。

```text
- MLOが正しい位置に表示されるか
- Materialが意図通り表示されるか
- ガラスやCutoutが破綻していないか
- Collisionが想定通りか
- Room / Portalが機能しているか
- 明るさや表示距離に問題がないか
```

問題が出たら、Blenderへ戻って修正します。

戻ったときの基本ループ:

```text
Blenderで修正
↓
Model PrepperでPreflight
↓
Material Assistantで再確認
↓
Sollumz ToolでExport
↓
CodeWalkerで確認
```

---

# よくある失敗とModel Prepperでの見つけ方

## Materialが真っ白・真っ黒になる

確認:

```text
- Material AssistantでMISSING_TEXTUREが出ていないか
- Image TextureがMaterialに割り当てられているか
- texture_namesが想定通りか
- Sollumz側で適切なShaderに変換したか
```

## ガラスや窓が変に表示される

確認:

```text
- Material AssistantでALPHAに分類されているか
- NORMAL_SPECにまとめて変換していないか
- 透明Materialとして手動確認したか
```

## フェンスや格子の抜きが出ない

確認:

```text
- Material AssistantでCUTOUTに分類されているか
- Cutout向けShader候補として確認したか
- Alpha/Cutout用のTextureになっているか
```

## Export後に形状が壊れる

確認:

```text
- Scale not appliedが残っていないか
- Complex Non-Manifoldが残っていないか
- Zero Area Facesが大量にないか
- Duplicate VerticesやLoose Geometryが残っていないか
```

## 見えるはずのObjectがExportされない

確認:

```text
- Export対象Objectを選択しているか
- Objectが非表示になっていないか
- Collection単位で非表示になっていないか
- Sollumz Export対象に含めているか
```

---

# 最小チェックリスト

## Blender作業中

```text
[ ] ObjectのScaleを確認した
[ ] 床・壁・天井の形状を作った
[ ] 窓・ドア穴のBoundaryを確認した
[ ] Zero Area Facesを確認した
[ ] Loose Geometryを確認した
[ ] UV Missingがないことを確認した
```

## Material作業中

```text
[ ] Analyze Materialsを実行した
[ ] NORMAL_SPEC候補を確認した
[ ] ALPHA候補を確認した
[ ] CUTOUT候補を確認した
[ ] MISSING_TEXTUREを解消した
[ ] MANUAL_REVIEWを確認した
[ ] Convert Allを blindly に押していない
```

## Export前

```text
[ ] Run Preflightを実行した
[ ] ERRORを解消した
[ ] WARNが意図したものか確認した
[ ] Export対象Objectを選択した
[ ] 非表示Objectが混ざっていないか確認した
[ ] Sollumz ToolでExportした
[ ] CodeWalkerで表示確認した
```

---

# 重要な考え方

Sollumz Model Prepperは、MLO制作を自動化するツールではありません。  
失敗しやすい箇所を事前に見つけて、Sollumz Toolでの手動作業を安全にするための補助ツールです。

```text
Sollumz Tool:
作る・設定する・Exportする

Sollumz Model Prepper:
検査する・分類する・選択しやすくする
```

この分担を守ると、作業が壊れにくくなります。
