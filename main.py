#  Copyright (c) 2021 Jan Westerhoff
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

from concurrent.futures import ProcessPoolExecutor

from algos import cycle_removel as cr, walker as wk, global_shift as gs, longest_path as lp, brand_koepf as bk
from helper_functions.graphml import GraphML


def walker_algo():
    wk.run('Data/Phylogeny-Binaer/7way.nh', figsize=(5, 10))
    wk.run('Data/Phylogeny-Binaer/ce11.26way.nh')
    wk.run('Data/Phylogeny-Binaer/hg38.20way.nh')
    wk.run('Data/Phylogeny-Binaer/hg38.100way.nh', figsize=(40, 20))
    wk.run('Data/Phylogeny-Binaer/eboVir3.160way.nh', figsize=(80, 40))
    wk.run('Data/Phylogeny/phyliptree.nh', figsize=(40, 40))
    wk.run('Data/Software-Engineering/Checkstyle-6.5.graphml', key='implementation')


def longest_path():
    lp.run('Data/Software-Engineering/Checkstyle-6.5.graphml', key='implementation')


def cycle_removal():
    cr.run('Data/Software-Engineering/Checkstyle-6.5.graphml', key='method-call')
    # cr.run('Data/Software-Engineering/JUnit-4.12.graphml', key='method-call')
    # cr.run('Data/Software-Engineering/Stripes-1.5.7.graphml', key='method-call')
    # cr.run('Data/Software-Engineering/JFtp.graphml', key='method-call')


def global_shifting():
    # files = ['Data/Software-Engineering/Checkstyle-6.5.graphml', 'Data/Software-Engineering/JUnit-4.12.graphml',
    #          'Data/Software-Engineering/Stripes-1.5.7.graphml', 'Data/Software-Engineering/JFtp.graphml']
    # nproc = 5
    #
    # with ProcessPoolExecutor(max_workers=nproc) as e:
    #     for file_name in files:
    #         for key in GraphML(file_name).keys():
    #             e.submit(gs.run, file_name, key, (160, 5))
    #
    # print('!---!')

    gs.run("TESTGRAPH.graphml", "TEST", (20, 20))


def brand_koepf():
    files = ['Data/Software-Engineering/Checkstyle-6.5.graphml', 'Data/Software-Engineering/JUnit-4.12.graphml',
             'Data/Software-Engineering/Stripes-1.5.7.graphml', 'Data/Software-Engineering/JFtp.graphml']
    nproc = 3

    with ProcessPoolExecutor(max_workers=nproc) as e:
        for file_name in files:
            for key in GraphML(file_name).keys():
                e.submit(bk.run, file_name, key, (60, 20), use_results=True, delta=0.3)

    # bk.run("TESTGRAPH.graphml", "TEST", (20, 20))
    # bk.run('Data/Software-Engineering/Checkstyle-6.5.graphml', 'inheritance', (60,20), use_results=True)


# def test():
#     G = digraph.DiGraph.load('result\Checkstyle-6.5\implementation\graph.dat')
#     print(G)

def main():
    # walker_algo()
    # longest_path()
    # cycle_removal()
    # global_shifting()
    brand_koepf()


if __name__ == '__main__':
    main()
