## 配置环境

在开始之前，请确保你的电脑上已经安装了下方任一环境管理器：
  * [Anaconda](https://www.anaconda.com/products/distribution) 或 [Miniconda](https://docs.conda.io/en/latest/miniconda.html)
  * [Python 3.9+](https://www.python.org/) 
---

### 第一步：克隆项目仓库

#### 方式一：直接下载 ZIP 包

1.  在项目主页，点击绿色的 **`< > Code`** 按钮。
2.  在弹出的菜单中，选择 **`Download ZIP`**。
3.  下载完成后，将这个 ZIP 文件解压到你希望存放项目的地方。
4.  打开Terminal 或命令提示符，使用 `cd` 命令进入到刚刚解压好的项目文件夹中。


#### 方式二：使用 Git 克隆

如果你熟悉 Git，也可以使用 `git clone` 命令。

```bash
git clone https://github.com/sealeelike/Enjoy-your-seat.git
cd Enjoy-your-seat
```

---

### 第二步：配置环境

#### 方案一：使用 Conda (如果你有conda环境)

```bash
conda env create -f environment.yml
conda activate ejys
```

#### 方案二：使用 Pip 和 venv

如果你不使用 Conda，可以使用 Python 内置的 `venv` 模块来创建虚拟环境。

1.  **创建虚拟环境**
    在项目根目录执行以下命令，这会创建一个名为 `venv` 的文件夹来存放虚拟环境。

    ```bash
    python -m venv venv
    ```

2.  **激活虚拟环境**
    * 在 **Windows** 上:
        ```bash
        venv\Scripts\activate
        ```
    * 在 **macOS 或 Linux** 上:
        ```bash
        source venv/bin/activate
        ```
    激活成功后，你会在终端提示符前看到 `(venv)` 字样。

3.  **安装依赖包**
    使用 `pip` 和 `requirements.txt` 文件来安装所有依赖。

    ```bash
    pip install -r requirements.txt
    ```

---

## 运行项目

在环境下，依次运行[programme](programme)文件夹内的python文件

#### 1-auth.py

这是爬取学校mrbs网站前的身份认证程序。

跟随提示完成登录即可，你会在项目文件夹里看到多出来一个`.env`和一个`area_mapping.json`文件。
> [!WARNING]
> 请看管好或及时删除这个些文件，因为里面有你的账号密码和学校内部数据

#### 2-getdata.py

它负责爬取相关的html页面。你会发现多了一个`pages_dd-mm-yyyy`文件夹。

同样的，请看管好它。

#### 3-html2rawdata.py

它负责把方才爬取到的`html`网页转化成`json`格式的数据

它会生成一个`data_dd-mm-yyyy`文件夹

#### 4-raw2vector.py

它负责优化刚刚得到的`json`数据。它会生成一个`ready_data_dd-mm-yyyy`文件夹

#### 5-main.py

这是主程序，会在选定的范围内，接连调用`sub.py`
