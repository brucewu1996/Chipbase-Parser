import pandas as pd 
import os,re,time,datetime,glob
import urllib.request,requests
#import asyncio,aiohttp,aiofiles,subprocess
from collections import deque
#from multiprocessing import Pool

class chipbase_parser :
    def __init__(self) :
        self.tf_list = None
        self.output_path = None
        self.upstream_range = None
        self.downstream_range = None
        self.upstream_range_options = ['1kb','5kb','10kb','20kb','30kb']
        self.downstream_range_options = ['1kb','2kb','5kb','10kb']

    def is_downloadable(self,url):
        """_summary_
        Args:
            url (str): target url
        Returns:
            boolean : this url is downloadable or not 
        """        
        h = requests.head(url, allow_redirects=True)
        header = h.headers
        content_type = header.get('content-type')
        if 'text' in content_type.lower():
            return False
        if 'html' in content_type.lower():
            return False
        return True

    def get_filename_from_response(self,response):
        """ Get the filename from request.response body
        Args:
            response (requests.models.Response): _description_
        Returns:
            str : filename of request content
        """        
        #assert response == requests.models.Response , "url is invalid!"
        if type(response) != requests.models.Response :
            print("url is invalid!")
            return
        if 'content-disposition' not in response.headers:
            print("content-disposition not in download url!")
            return 
        fname = re.findall('filename=(.+)', response.headers.get('content-disposition'))
        return fname[0]

    def download_files(self,page,assembly,experiment_id,max_retry=5) :
        """
        Batch download target TF information from chipbase3.0 for specific domain/experiment/reference.
        Args:
            page (str): Domain of Chipbase3.0.
            assembly (str): Reference version.
            experiment_id (str): Experiment ID.
            max_retry (int): Number of download retry. Defaults to 5.
        """
        if not self.upstream_range or not self.downstream_range :
            print("Without upstream or downstream range !")
            return 
        if self.upstream_range not in self.upstream_range_options :
            print("Please set upstream range in following options : '1kb','5kb','10kb','20kb','30kb'.")
            return 
        if self.downstream_range not in self.downstream_range_options :
            print("Please set downstream range in following options : '1kb','2kb','5kb','10kb'.")
            return 
        if not self.tf_list :
            print("TF list is blank !")
            return 
        #create a deque for waited TF
        download_list = deque(self.tf_list.copy())
        retry_dict = {key :0 for key in self.tf_list}

        while download_list :
            target = download_list.popleft()
            download_url = "https://rnasysu.com/chipbase3/download.php?base_page=%s&assembly=%s&protein=%s&sample_id=%s&type=protein&upstream=%s&downstream=%s&motif_status=N&Ftype=tab" % (page,assembly,target,experiment_id,self.upstream_range,self.downstream_range)
            if self.is_downloadable(download_url) :
                r = requests.get(download_url, allow_redirects=True)
                filename = self.get_filename_from_response(r)
                if filename :
                    urllib.request.urlretrieve(download_url,self.output_path+filename)
                    # check download status
                    if os.path.isfile(self.output_path+filename) :
                        prefix = filename.split('without_motif')[0]
                        os.system("tail -n +8 %s > %s" % (self.output_path + filename,self.output_path + prefix + '.txt'))
                        del retry_dict[target]
                    else :
                        retry_dict[target] += 1
                        if retry_dict[target] > max_retry :
                            del retry_dict[target]
                        else :
                            download_list.append(target)
                else :
                    retry_dict[target] += 1
                    if retry_dict[target] > max_retry :
                        del retry_dict[target]
                    else :
                        download_list.append(target)
            else :
                retry_dict[target] += 1
                if retry_dict[target] > max_retry :
                    del retry_dict[target]
                else :
                    download_list.append(target)

class async_chipbase_parser :
    def __init__(self) :
        self.url_list = []
        self.output_path = None
        self.upstream_range = None
        self.downstream_range = None
        self.page = None
        self.assembly = None
        self.upstream_range_options = ['1kb','5kb','10kb','20kb','30kb']
        self.downstream_range_options = ['1kb','2kb','5kb','10kb'] 

    def create_url_list(self,tf_list,experiment_id) :
        for tf in tf_list :
            #self.page,self.assembly,tf,experiment_id,self.upstream_range,self.downstream_range
            download_url = f"https://rnasysu.com/chipbase3/download.php?base_page={self.page}&assembly={self.assembly}&protein={tf}&sample_id={experiment_id}&type=protein&upstream={self.upstream_range}&downstream={self.downstream_range}&motif_status=N&Ftype=tab" 
            self.url_list.append(download_url)

    async def download_process(self,session,url,output_path):
        """ Download chipbase attach file by aiohttp
        Args:
            session (aiohttp.ClientSession): seccsion create by aiohttp
            url (str): download url
            output_path (str): path of output folder
        """
        try :        
            resp = await session.get(url,allow_redirects=True)
            if resp.status == 200 :
                if 'Content-Disposition' in resp.headers :
                    filename = resp.headers['Content-Disposition'].split('=')[-1]
                    content = await resp.read()
                    async with aiofiles.open(output_path + filename, "ba") as f:
                        await f.write(content)
                    #remove first 7 line of chipbase parser result
                    prefix = filename.split('_protein_regulations')[0]
                    tail_process = await asyncio.create_subprocess_shell("tail -n +8 %s" % output_path + filename,stdout=open(output_path + prefix + '.txt', 'w'))
                    await tail_process.wait()
                    '''
                    status = subprocess.call(['test','-f',output_path+filename]) 
                    if status == 0:
                        prefix = filename.split('_protein_regulations')[0]
                        subprocess.call(["tail",'-n','+8',output_path + filename],stdout=open(output_path + prefix + '.txt', 'w'))
                        subprocess.call(['rm',output_path + filename])
                    '''
            return "Download completed"
        except asyncio.exceptions.TimeoutError as e:
            return e

    async def url_parser(self):
        if self.url_list == [] :
            print("Please create url list by create_url_list function first!")
            return 
        conn = aiohttp.TCPConnector(ssl=False)  # 防止ssl报错
        async with aiohttp.ClientSession(connector=conn) as session:
            # 建立所有任务
            loop = asyncio.get_event_loop()
            tasks = [asyncio.create_task(self.download_process(session,url,self.output_path)) for url in self.url_list]
            # 触发await，等待任务完成
            complete,uncomplete = loop.run_until_complete(asyncio.wait(tasks))
            loop.close()

class chipbase_result_formater :
    """ 
    Class for format chipbase output result
    """    
    def __init__(self,result_path,biomart_info,output_path) :
        self.result_path = result_path
        self.biomart_dict = biomart_info
        self.output_path = output_path

    def format_chipbase_result(self,filename) :
        """
        Args:
            filename (str): filename of un-formated result
        """        
        tf_name = filename.split('_')[3]
        if '-' in tf_name :
            return
        df = pd.read_csv('%s' % (filename),sep='\t',index_col=0)
        nrow = df.shape[0]
        df['TF_name'] = [tf_name] * nrow
        if tf_name in self.biomart_dict :
            df['TF_GeneID'] = [self.biomart_dict[tf_name]['Gene stable ID']] * nrow
        else :
            df['TF_GeneID'] = [None] * nrow
        # Define the container of values
        for idx in range(nrow) :
            gene_symbol = df['GeneSymbol'].values[idx]
            if gene_symbol in self.biomart_dict :
                df['GeneChromosome'] = self.biomart_dict[gene_symbol]['Chromosome/scaffold name'] 
                df['GeneStart'] = self.biomart_dict[gene_symbol]['Gene start (bp)'] 
                df['GeneEnd'] = self.biomart_dict[gene_symbol]['Gene end (bp)'] 
                df['GeneStrand'] = self.biomart_dict[gene_symbol]['Strand']
        df.to_csv("%s/%s" % (self.output_path,filename.split('/')[-1]),sep='\t')

    def multiple_processing_chipbase_result(self,n_threads = 12) :
        file_list = glob.glob("%s/*[_without_motif].txt" % self.result_path)
        print(f'{len(file_list)} unformated file exist')
        pool = Pool(n_threads)
        pool.map(self.format_chipbase_result, file_list) 
        pool.close()
        pool.join()

    def batch_processing_chipbase_result(self) :
        file_list = glob.glob("%s/*[_without_motif].txt" % self.result_path)
        print(f'{len(file_list)} unformated file exist')
        for f in file_list :
            tf_name = f.split('_')[3]
            self.format_chipbase_result(f)
    

def main() :
    #load requirement information
    gene_list = pd.read_csv("material/coding_gene_symbol.txt",header=None)
    gene_list.columns = ['Gene symbol']
    exp_df = pd.read_excel("material/chipbase_experiment.xlsx")
    experiments = exp_df.ChipbaseID.values
    #load biomart information
    biomart = pd.read_csv("material/biomart_v110_protein_coding_gene_information_20231201.txt",sep='\t',index_col=9,low_memory=False)
    biomart_info = biomart.loc[:,['Gene stable ID','Chromosome/scaffold name','Gene start (bp)','Gene end (bp)','Strand']]
    biomart_dict = biomart_info.drop_duplicates().T.to_dict()

    #set input/output path
    result_path = "chipbase_result/"
    os.makedirs(result_path,exist_ok=True)

    for idx,experiment in enumerate(experiments) :
        print("Parse chipbase information for experiment : %s at %s" % (experiment,datetime.datetime.now().strftime("%Y/%m/%d-%H:%M:%S")))
        dt = datetime.datetime.now()
        #Inititalation 
        result_output_path = result_path + experiment + '/'
        if os.path.isdir(result_output_path) == False :
            os.mkdir(result_output_path)
        
        parser = chipbase_parser()
        parser.downstream_range = '1kb'
        parser.upstream_range = '1kb'
        parser.output_path = result_output_path 
        parser.tf_list = list(gene_list['Gene symbol'].unique())
        parser.download_files("regulation_browse","hg38",experiment,max_retry=1)
    
        ''' asynchrous version (not recommanded!)
        parser = async_chipbase_parser()
        parser.downstream_range = '1kb'; parser.upstream_range = '1kb'
        parser.page = "regulation_browse"; parser.assembly = "hg38"
        parser.output_path = result_output_path 
        tf_list = list(gene_list['Gene symbol'].unique())
        #execute asynchronous processing
        parser.create_url_list(tf_list,experiment)
        parser.url_parser()

        loop = asyncio.get_event_loop()
        loop.run_until_complete(parser.url_parser())
        loop.close()
        '''
        dt_end = datetime.datetime.now()
        print("Parse chipbase information for experiment : %s completed at %s, execution time : %s" % (experiment,datetime.datetime.now().strftime("%Y/%m/%d-%H:%M:%S"),str(dt_end-dt)))
        print("Format chipbase information for experiment : %s is completed at %s" % (experiment,datetime.datetime.now().strftime("%Y/%m/%d-%H:%M:%S")))
        #format chipbase result
        '''
        format_output_path = formated_path + experiment
        if os.path.isdir(format_output_path) == False :
            os.mkdir(format_output_path)

        formater = chipbase_result_formater(result_path=result_output_path,
                biomart_info=biomart_dict,
                output_path=format_output_path)
        formater.multiple_processing_chipbase_result(n_threads=32)

        print("Chipbase information for experiment (%d/%d) : %s is completed at %s" % (idx+1,len(experiments),
        experiment,datetime.datetime.now().strftime("%Y/%m/%d-%H:%M:%S")))
        '''

if __name__ == '__main__' :
    main()