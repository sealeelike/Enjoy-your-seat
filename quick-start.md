## Environment Setup

Before you begin, ensure that one of the following is installed on your system:

  * [Anaconda](https://www.anaconda.com/products/distribution) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html)
  * [Python 3.9+](https://www.python.org/)

-----

### Step 1: Clone the Project Repository

#### Option 1: Download the ZIP file

1.  On the main project page, click the green **`< > Code`** button.
2.  From the dropdown menu, select **`Download ZIP`**.
3.  Once the download is complete, extract the ZIP file to your desired project location.
4.  Open your Terminal or Command Prompt and use the `cd` command to navigate into the extracted project folder.

#### Option 2: Clone with Git

If you are familiar with Git, you can use the `git clone` command.

```bash
git clone https://github.com/sealeelike/Enjoy-your-seat.git
cd Enjoy-your-seat
```

-----

### Step 2: Set Up the Environment

#### Option 1: Using Conda

If you are using Conda, run the following commands:

```bash
conda env create -f environment.yml
conda activate ejys
```

#### Option 2: Using Pip and venv

If you do not use Conda, you can create a virtual environment using Python's built-in `venv` module.

1.  **Create a virtual environment**
    From the project's root directory, run the following command. This will create a folder named `venv` to store the virtual environment.

    ```bash
    python -m venv venv
    ```

2.  **Activate the virtual environment**

      * On **Windows**:
        ```bash
        venv\Scripts\activate
        ```
      * On **macOS or Linux**:
        ```bash
        source venv/bin/activate
        ```

    Once activated, you should see `(venv)` preceding your terminal prompt.

3.  **Install dependencies**
    Install all required packages using `pip` and the `requirements.txt` file.

    ```bash
    pip install -r requirements.txt
    ```

-----

## Running the Project

With the environment activated, run the Python scripts in the `programme` folder in the following order:

#### 1-auth.py

This script handles authentication before scraping the school's MRBS website.

Follow the prompts to complete the login process. Upon success, a `.env` file and an `area_mapping.json` file will be created in the project directory.

> [\!WARNING]
> Please safeguard or delete these files promptly, as they contain your account credentials and internal school data.

#### 2-getdata.py

This script is responsible for scraping the relevant HTML pages. You will notice a new folder named `pages_dd-mm-yyyy` has been created.

Similarly, please handle this folder with care.

#### 3-html2rawdata.py

This script converts the previously scraped HTML pages into JSON format.

It will generate a folder named `data_dd-mm-yyyy`.

#### 4-raw2vector.py

This script processes and optimizes the JSON data. It will generate a folder named `ready_data_dd-mm-yyyy`.

#### 5-main.py

This is the main program. It sequentially calls `sub.py` to perform its primary functions within a selected scope.
