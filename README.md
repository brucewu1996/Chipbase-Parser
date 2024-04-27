# Chipbase-Parser
The parser for chipbase 3.0[https://rnasysu.com/chipbase3/] information
### Requirement
1. pandas
2. urllib
3. aiofiles,aiohttp (optional)
### Parameters
* The naming rule of Chipbase download url like :
    https://rnasysu.com/chipbase3/download.php?base_page=%s&assembly=%s&protein=%s&sample_id=%s&type=protein&upstream=%s&downstream=%s&motif_status=N&Ftype=tab
    * It have multiple input parameter including :
        1. page = regulation_browse
        2. assembly = hg38
        3. protein = name of target transcirption factor. (material/tf_list.txt)
        4. sample_id = Chipbase experiment ID. (material/chipbase_experiment.xlsx)
        5. upstream
        6. downstream
    * Notice !! The tf_name / protein_name of chipbase 3.0 may contain multiple tf/proteins separated by '-'. (e.g. RPL17-C18orf32) Those tf/protein record in material/dashed_tf_list.txt
