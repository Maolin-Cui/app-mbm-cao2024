# Cao et al. 2024 原版 MBM 的 Brainlife 群体分析适配包（准备版）

**状态：可检查群体输入、生成原版工具所需的设计矩阵与列表；不代表已经在 Brainlife 集群上完成端到端测试。**

## 科学方法
- 论文：Cao T et al. *Mode-based morphometry: A multiscale approach to mapping human neuroanatomy*. Human Brain Mapping. 2024. DOI:10.1002/hbm.26640。
- 原版工具：https://github.com/NSBLab/MBM （Apache 2.0）；入口 `mbm_main.m`。
- 该包**不重新实现**置换、模态分解、FDR 或统计重建，而由原版 `mbm_main.m` 执行。
- fsLR-32k midthickness 共同模板；每半球 150 个模态；ANCOVA_Z；5000 permutations；FDR。
- `case=1` / `control=2`，并纳入年龄、性别。真正的有向组间差异正负定义必须对照代码验证，不能只凭符号推断。

## 核心限制
你的 Brainlife FreeSurfer 7.3.2 输出**通常是个体原始表面**，不是 32k_fsLR。不能直接把 `.thickness` 当作 32k 同模板输入。
要先进行以下额外步骤：

1. 每个对象做标准化结构质控（白质、皮层外表面、拓扑/medial wall）。
2. 使用受验证的 FreeSurfer→fsLR-32k 映射流程（如 HCP/ciftify，需核实软件版本与所用表面对齐）。
3. 将左右皮层厚度 `.func.gii` 投射到**同一个** 32k fsLR 顶点排列。
4. 下载 Cao 官方 OSF 示例数据中的 fsLR-32k 对应 `mask`、`eigenmodes`、`mass`、`vtk`，左右半球各一套；如果官方没有右半球匹配文件，不要自行复用左半球文件。
5. 各个受试者的组别、年龄、性别写入 `subjects.csv`。案例与对照组别不能因为分属不同 Brainlife 项目而混乱。

若上述任一步无法满足，**停止运行**，不能把输出称为论文复现的 MBM。

## 输入目录结构
将所有需要群体比较的对象在**获授权的数据环境**中打包成 `group_bundle`（Brainlife `raw` 数据集；该脚本不会自动跨项目抓取原始影像）：

```
group_bundle/
  subjects.csv
  maps/
    sub-001.L.thickness.32k_fsLR.func.gii
    sub-001.R.thickness.32k_fsLR.func.gii
    ...
  template/
    lh.mask.txt
    lh.eig.txt
    lh.mass.mat
    lh.surf.vtk
    rh.mask.txt
    rh.eig.txt
    rh.mass.mat
    rh.surf.vtk
```

`subjects.csv` 列：`subject_id,group,age,sex,lh_map,rh_map`；`sex` 为 `M/F`，无缺失。文件路径相对 `group_bundle`。

`lh.eig.txt`、`lh.mass.mat` 等是**为适配层统一重命名**的文件；来源必须是官方相应 32k 模板，不得空文件占位。顶部 `example_subjects.csv` 是字段示例，不是真实数据。

## GitHub 环境准备

本 zip 不捆绑作者工具箱，也不捆绑 2 GB 的模板示例数据。
在开发电脑联网执行：

```
./install_official_mbm.sh
```

保留官方许可证并记录 `MBM_UPSTREAM_COMMIT.txt`，在开发用的 GitHub repo 里提交官方源码，或者用 Git submodule 并确保集群支持 submodule 检出。注意许可证和体积限制。

## 本地预检

```
cp config.json.sample config.json
# 编辑 config.json 的 group_bundle 指向你的实际目录
python3 prepare_inputs.py --config config.json
```

期望生成：
- `prepared/included_subjects.csv`
- `prepared/design_ANCOVA.txt`
- `prepared/lh_input_maps.txt`
- `prepared/rh_input_maps.txt`
- `prepared/preflight_report.json`

**预检只检查文件存在、组别、数量、mask 大小等，不证明图像真的是正确的 fsLR 空间。**

## Brainlife New App 注册

这次与旧版不同：**这是群体 App，不应该使用每人一个 `neuro/freesurfer` 输入的 Pipeline Rule。**

1. 先在 Brainlife 内备齐一个 `raw` 型的群体数据集（里面含全部组的图和模板），运行单个 Group App 任务。
2. `Configurations`：
   - String `case_label` = `MSA`
   - String `control_label` = `HC`
   - Number `num_modes` = `150`
   - Number `n_permutations` = `5000`
   - Number `p_threshold` = `0.05`
   - Number `gpd_p_threshold` = `0.1`
   - Boolean `fdr` = `true`
3. `Inputs`：`raw` 群体 bundle，File mapping **JSON key 必须为 `group_bundle`**；路径需要匹配你实际打包方式。
4. `Outputs`：开发期可用 `raw`，输出路径 `result/`；后面稳定后申请正式数据类型。
5. MATLAB R2022a–R2024a 及许可证：向计算资源管理员确认；App 注册并不自动提供 MATLAB。官方 Brainlife 文档明确需要资源管理员 enable App。
6. 前期先每组少量数据验证 `mbm_main.m`、空间对应关系和两个半球结果，再做正式 5000 permutations。

如群体数据需从多个项目汇总，请先在具有权限的环境内准备好 group bundle。不要将受限的 ADNI/PPMI 原始数据未经明确许可上传到 Brainlife。

## 为什么不能在当前 New App 直接输入 `save_modes=20`

`save_modes` 是前一个自编个体几何 QC 工具的参数；Cao 原版 MBM 没有这一参数。Cao 的原版主要统计产物是 `MBM.eig.beta`、`pBeta`、`significantBeta` 和 `reconMap`。原版 `mbm_main.m` 可以保存完整的 MBM 结构。

## 下一步必须验证
- 正式模板及 mass matrix 左右对应关系和顶点顺序；
- 参考版本和 MATLAB 环境；
- 皮层厚度平滑的预先定义及控制组/病例对比方向；
- 置换检验中协变量处理与独立测试对照结果；
- 同一批样本与传统 SBM 的差异图和重建的一致性；
- 左右半球各自 FDR 还是全 300 模态 FDR 的分析口径（原版默认行为以代码为准）。

只有通过验证后才可称“与 Cao 2024 官方 MBM 工具一致的方法学实现”。
