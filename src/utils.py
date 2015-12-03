import sys,os
import subprocess
import multiprocessing


def test_fun(a, b):
    print '%s says that %s' % (multiprocessing.current_process().name, str(a)+','+str(b))

def run_multiprocess_cb(cb_func, args):
    cb_func(*args)

def run_multiprocess_cb_wrapper(args):
    return run_multiprocess_cb(*args)

class Utils():
    """
    Some Utility Functions
    """
    def __init__(self):
        pass


    def gen_runcPy_script(self, program, input_list, output_list, output_path, replace=False):
        """
        Generate the runcPy script

        @Input:
            program (list) - the list of programs that will be executed by runcPy
            input_list (list) - The input list for runcPy
            output_list (list) - The output list for runcPy
            output_path (string) - The output path the script
            replace (boolean) - if the output file exists, whether replace it

        @Return: no return. the output will be the script file
        """

        node_cnt = 8
        with open(output_path, 'wb') as output:
            output.write('#!/bin/sh\n')
            output.write('shopt -s expand_aliases\n')
            output.write('alias runcPy="/infolab/headnode/ypeilin/bin/mpiexec -f /infolab/headnode/ypeilin/machinefile -n 8 python /infolab/headnode/ypeilin/runC.py -vc"\n')

            program_idx = 0
            for i in range(0, len(input_list), node_cnt):
                output.write('runcPy "%s [' % str(program[program_idx]))
                for j in range(i, min(len(input_list), i+node_cnt)):
                    output.write('%s ' % (input_list[j]))
                output.write(']')
                if len(output_list) > 0:
                    output.write(' > [')
                    for j in range(i, min(len(input_list), i+node_cnt)):
                        output.write('%s ' % (output_list[j]))
                    output.write(']"\n')
                else:
                    output.write('"\n')

                program_idx += 1

        subprocess.call(['chmod', 'a+x', output_path])


    def run_multiprocess_program(self, cb_function, args):
        """
        run the multiprocess program on headnode

        @Input:
            cb_function - the callback function
            args (list of lists) - the arguments for the callback funtion 
        """

        cb_and_args = []
        for ele in args:
            cb_and_args.append((cb_function, ele))
        pool = multiprocessing.Pool(processes=8)
        pool.map(run_multiprocess_cb_wrapper, cb_and_args)



if __name__ == '__main__':
    u = Utils()
    #u.gen_runcPy_script('ls -l', [1,2,3,4,5,6,7,8,9,10], ['o1','o2','o3','o4','o5','o6','o7','o8','o9','o10'], './tmp')
    #u.gen_runcPy_script('ls -l', [1,2,3,4,5,6,7,8,9,10], [], './tmp')
    u.run_multiprocess_program(test_fun, [[1,2],[3,4],[5,6]])




