"""Framework for Intelligent Agents Development - PADE

The MIT License (MIT)

Copyright (c) 2019 Lucas S Melo

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

from twisted.internet import reactor, threads
from twisted.internet.endpoints import TCP4ServerEndpoint
# import pade.core.agent as N

from datetime import datetime
import click

def display_message(name, data):
    """
        Method do displsy message in the console.
    """
    date = datetime.now()
    date = date.strftime('%d/%m/%Y %H:%M:%S.%f')[:-3]
    click.echo(click.style('[{}] {} --> '.format(name, date), fg='green') + str(data))
    # print('[' + name + '] ' + date + str(data))


def call_in_thread(method, *args):
    """
        Call blocking method in another thread
    """
    reactor.callInThread(method, *args)


def call_later(time, method, *args):
    """
        Call method in reactor thread after timeout
    """
    return reactor.callLater(time, method, *args)


def defer_to_thread(block_method, result_method, *args):
    """
        Call blocking method in another thread passing callback
    """
    d = threads.deferToThread(block_method, *args)
    d.addCallback(result_method)


def call_from_thread(method, *args):
    """
        Call reactor method (usually not thread safe) from thread
    """
    reactor.callFromThread(method, *args)


def start_loop(agents):
    """Start reactor thread main loop"""
    reactor.suggestThreadPoolSize(1)
    for agent in agents:
        agent.update_ams(agent.ams)
        agent.on_start()
        endpoint = TCP4ServerEndpoint(reactor, agent.aid.port)
        # node = Node(endpoint, reactor, agent.agentInstance)
        # node.listen()
        endpoint.listen(agent.agentInstance)
        ILP = reactor.listenTCP(agent.aid.port, agent.agentInstance)
        agent.ILP = endpoint
    reactor.run()


def print_progress_bar(iteration, total, prefix='', suffix='', decimals=1, length=100, fill='█', printEnd="\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print('%s |%s| %s%% %s' % (prefix, bar, percent, suffix))
    # Print New Line on Complete
    # if iteration == total:
    #     print()


def start_single_agent(agent):
    agent.update_ams(agent.ams)
    agent.on_start()
    endpoint = TCP4ServerEndpoint(reactor, agent.aid.port)
    node = Node(endpoint, reactor, agent.agentInstance)
    node.listen()
    agent.ILP = endpoint

def stop_agent(agent):
    agent.agentInstance.stopListening()

