# Chipbase-Parser
The parser for [chipbase 3.0](https://rnasysu.com/chipbase3/) transcription factor information.
---
*Requirement
1. pandas
2. urllib
3. aiofiles,aiohttp (optional)
---
*Parameters
    * The naming rule of Chipbase download url like :
        https://rnasysu.com/chipbase3/download.php?base_page=%s&assembly=%s&protein=%s&sample_id=%s&type=protein&upstream=%s&downstream=%s&motif_status=N&Ftype=tab
    * It have multiple input parameter including :
        1. page = regulation_browse
        2. assembly = hg38
        3. protein = name of target transcirption factor. (material/tf_list.txt)
        4. sample_id = Chipbase experiment ID. (material/chipbase_experiment.xlsx)
        5. upstream
        6. downstream
    >Notice !! The tf_name / protein_name of chipbase 3.0 may contain multiple tf/proteins separated by '-'. (e.g. RPL17-C18orf32) Those tf/protein record in material/dashed_tf_list.txt
---
*Program logic
1. Use request & urllib to create the corresponding download url.
2. Put the target tfs into a deque. (First in First out list)
3. Send the download request to Chipbase.
4. Confirm the download request is succes or not. (invalid url or other network issue.)
5. If download request is fail, pop the target tf from deque, and add it into the end of deque. (If the number of retry of this tf is not reach the max_retry)
6. Pause the download process 0.5 seconds after each request. (To avoid the request limitation of Chipbase 3.0)
---
*Usage
Please modify the following variable in main function of chipbase_parser.py :
1. gene_list (The target tf_list. Default is material/tf_list.txt)
2. experiment_list (The text / excel file record the experiment ID of Chipbase 3.0. Default is material/chipbase_experiment.xlsx)
3. result_path (Output path)