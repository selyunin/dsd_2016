#!/usr/bin/python

# This script:
# 1 reads the source file
# 2 replaces the commented line with assert statement with a counter value 
# 2 writes the instantiated file
# 3 launches cbmc on function specified from command input
# 4 extracts values of parameters in counterexample
# 5 generates a test file with the values inserted
# 6 visualizes spikes and membrane potential over time

import os
import re
import sys
import csv
import argparse
import cmd, sys
import datetime
import shutil 
import tempfile 
import subprocess 
from lxml import etree as ET
import numpy as np
import matplotlib.pyplot as plt

variables = ['w', 's', 'epsilon', 'lambda', 'alpha', 'beta', 'R', 'gamma', 'kappa']
parameters = dict()

def call_cbmc(source_file, function, log_fname):
    PWD = os.getcwd() + '/../bin'
    cbmc_cmd = [PWD + '/cbmc', source_file, '--function', function, '--xml-ui']
    print cbmc_cmd
    log_file = open(log_fname, 'w')
    exit_code = subprocess.call(cbmc_cmd, stdout=log_file)
    log_file.close()
    params_found = False
    if exit_code == 10:
        print "parameter values found"
        params_found = True
    elif exit_code == 0:
        print "NO parameter values found"
        params_found = False
    return params_found
    
def extract_values(log_file):
    xml_data = open(log_file, 'r')
    tree = ET.parse(xml_data)
    for assignment in tree.xpath('//assignment'):
        #counter example variables and values
        ce_var = assignment.xpath('child::full_lhs')[0].text
        ce_val = assignment.xpath('child::full_lhs_value')[0].text
        if ce_var in variables and ce_var not in parameters.keys():
            parameters[ce_var]  = ce_val
    print parameters
    xml_data.close()

def replace(file_path, pattern, subst):
    #Create temp file
    fh, abs_path = tempfile.mkstemp()
    with open(abs_path,'w') as new_file:
        with open(file_path) as old_file:
            for line in old_file:
                new_file.write(re.sub(pattern,subst,line))
    os.close(fh)
    #Remove original file
    os.remove(file_path)
    #Move new file
    shutil.move(abs_path, file_path)

def read_csv(filename):
    arr_out = []
    with open(filename, 'rb') as csvfile:
        content = csv.reader(csvfile, delimiter=',')
        for row in content:
            line = []
            for n in range(len(row)):
                line.append(int(row[n]))
            arr_out.append(line)
    return np.array(arr_out)

def parse(argv):
    #parse cmd arguments
    parser = argparse.ArgumentParser(description='Use cbmc to find parameters of the counter-example')
    parser.add_argument("-s", "--source")
    parser.add_argument("-f", "--function")
    parser.add_argument("-n", "--num_spikes", type=int)
    return parser.parse_args(argv)

def create_testfile(src_file, test_file, out_file):
    test_file_c = test_file + '.c'
    shutil.copy(src_file, test_file_c) 
    replace(test_file_c, '.*//DEFINE_TEST.*', '#define TEST')
    replace(test_file_c, '.*//INSERT_FILE_NAME.*', 'const char* fname = \"' + out_file + '\";')
    for key in parameters.keys():
        replace(test_file_c, '^.*//substitute_'+ key, parameters[key])

def compile(fname):
    #invoke gcc on the file and return exit flag
    gcc_call = [ 'gcc', fname + '.c', '-o', fname , '-std=c99']
    log_file = open( fname + '_compile_log', 'w')
    exit_code = subprocess.call(gcc_call, stdout=log_file)
    return exit_code
    
def visualize(csv_fname, plot_fname):
    vals = read_csv(csv_fname)
    t = vals[:,0]
    V = vals[:,1]
    S = vals[:,2]
    fig_no = 1
    plt.figure(fig_no)
    fig_no += 1
    plt.subplot(2,1,1)
    plt.ylabel('membrane potential')
    plt.plot(t, V, '-', color='blue')
    plt.plot(t, int(parameters['alpha'])*np.ones(len(t)), '-', color='red')
    plt.ylim(0,max(np.append(V, int(parameters['alpha']))))
    plt.subplot(2,1,2)
    plt.ylabel('output spikes')
    plt.plot(t, S*3, 'o', color='red')
    plt.ylim(0.5,3.5)
    plt.savefig(plot_fname, bbox_inches='tight')
    plt.show()

def main(argv):
    args = parse(argv)

    src = ""
    spike_num = 0
    fcn = ""
    
    if (args.function == None or args.num_spikes == None or args.source == None ):
        src = "c_src/assert_ex"
        spike_num = 33
        fcn = "fcn"
    else:
        src = re.match('^[\w/]*', args.source).group(0)
        spike_num = args.num_spikes
        fcn = args.function
    
    src_file = src + ".c"
    time_stamp = datetime.datetime.now().strftime("_%Y_%m_%d_%H_%M_%S")
    instr_file = src + time_stamp + ".c"
    test_file  = src + time_stamp + "_test"
    out_file   = test_file + '_out.csv'
    log_file   = src + time_stamp + '_log' 
    #create instrumented source file 
    shutil.copy(src_file, instr_file) 
    replace(instr_file, '//ASSERT_STATEMENT.*', 'assert(cnt != ' + str(spike_num) + ');')
    #call cbmc
    print "calling cbmc"
    params_found = call_cbmc(instr_file, fcn, log_file)
    print "call finished cbmc"
    print "parameter found = " + str(params_found)
    #extract values
    if(params_found):
        extract_values(log_file)
        print "values extracted"
        #generate test file
        create_testfile(src_file, test_file, out_file)
        exit_code = compile(test_file)
        print "compiled"
        if(exit_code == 0):
            #execute compiled c binary
            print "executing test file"
            print test_file
            subprocess.call(os.getcwd() + '/' + test_file)
            print "executing test file done..."
            visualize(out_file, 'img/plot.pdf')
    print "Bye...;"
    
if __name__ == "__main__":
    main(sys.argv[1:])
