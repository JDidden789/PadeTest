import random

from pade.misc.utility import display_message, start_single_agent, stop_agent
from pade.core.agent import Agent
from pade.acl.aid import AID
from pade.acl.messages import ACLMessage
from pade.behaviours.protocols import FipaContractNetProtocol, FipaSubscribeProtocol
from pade.behaviours.protocols import TimedBehaviour
from pade.core.Organization import Organization
from pade.misc.common import PadeSession

from twisted.internet import reactor

from sys import argv
from random import uniform


class SubscriberProtocolMachine(FipaSubscribeProtocol):
    """SubscriberProtocolMachine

       Subcriber Protocol allowing agents to request to be subscribed to another agent
       in order to receive certain messages, CFPS, etc..."""

    def __init__(self, agent, message):
        super(SubscriberProtocolMachine, self).__init__(agent,
                                                        message,
                                                        is_initiator=True)

    def handle_agree(self, message):
        display_message(self.agent.aid.name, message.content)

    def handle_inform(self, message):
        display_message(self.agent.aid.name, 10.0)


class PublisherProtocolMachine(FipaSubscribeProtocol):
    """PublisherProtocolMachine

       Publisher Protocol allowing agents to subsribe to this agent
       in order to receive certain messages, CFPS, etc..."""

    def __init__(self, agent):
        super(PublisherProtocolMachine, self).__init__(agent,
                                                       message=None,
                                                       is_initiator=False)
        self.agent = agent

    def handle_subscribe(self, message):
        self.register(message.sender)
        display_message(self.agent.aid.name, message.content)
        response = message.create_reply()
        response.set_performative(ACLMessage.AGREE)
        response.set_content('Subscribe message accepted')
        self.agent.send(response)

    def handle_cancel(self, message):
        self.deregister(message.sender)
        display_message(self.agent.aid.name, message.content)

    def notify(self, message):
        super(PublisherProtocolMachine, self).notify(message)


class JobBidRequest(FipaContractNetProtocol):
    """JobBidRequest

       Initial FIPA-ContractNet Behaviour that sends CFP messages
       to Machine Agents asking for job bidding proposals.
       This behaviour also analyzes the proposals and selects the
       one it judges to be the best."""

    def __init__(self, agent):
        super(JobBidRequest, self).__init__(
            agent=agent, message=None, is_initiator=True)
        display_message(self.agent.aid.name, 'Sending proposals...')

    def handle_all_proposes(self, proposes):
        """
        Function that looks at the received proposals,
        anlaysis them and chooses the best one.
        """

        super(JobBidRequest, self).handle_all_proposes(proposes)

        best_proposer = None
        higher_power = 0.0
        other_proposers = list()
        display_message(self.agent.aid.name, 'Analyzing proposals...')

        i = 1

        # logic to select proposals by the higher available power.
        for message in proposes:
            content = message.content
            power = float(content)
            display_message(self.agent.aid.name,
                            'Analyzing proposal {i}'.format(i=i))
            display_message(self.agent.aid.name,
                            'Power Offered: {pot}'.format(pot=power))
            i += 1
            if power > higher_power:
                if best_proposer is not None:
                    other_proposers.append(best_proposer)

                higher_power = power
                best_proposer = message.sender
            else:
                other_proposers.append(message.sender)

        display_message(self.agent.aid.name,
                        'The best proposal was: {pot} VA'.format(
                            pot=higher_power))

        if other_proposers:
            display_message(self.agent.aid.name,
                            'Sending REJECT_PROPOSAL answers...')
            answer = ACLMessage(ACLMessage.REJECT_PROPOSAL)
            answer.set_protocol(ACLMessage.FIPA_CONTRACT_NET_PROTOCOL)
            answer.set_content('')
            for agent in other_proposers:
                answer.add_receiver(agent)

            self.agent.send(answer)

        if best_proposer is not None:
            display_message(self.agent.aid.name,
                            'Sending ACCEPT_PROPOSAL answer...')

            answer = ACLMessage(ACLMessage.ACCEPT_PROPOSAL)
            answer.set_protocol(ACLMessage.FIPA_CONTRACT_NET_PROTOCOL)
            answer.set_content('OK')
            answer.add_receiver(best_proposer)
            self.agent.send(answer)

    def handle_inform(self, message):
        """
        """
        super(JobBidRequest, self).handle_inform(message)

        display_message(self.agent.aid.name, 'INFORM message received')

    def handle_refuse(self, message):
        """
        """
        super(JobBidRequest, self).handle_refuse(message)

        display_message(self.agent.aid.name, 'REFUSE message received')

    def handle_propose(self, message):
        """
        """
        super(JobBidRequest, self).handle_propose(message)

        display_message(self.agent.aid.name, 'PROPOSE message received')

    def notify(self, message):
        particapants = self.agent.subProtocal.get_partial_subscribers("machine")
        for sub in particapants:
            message.add_receiver(sub)
        super(JobBidRequest, self).notify(message)


class JobBidResponse(FipaContractNetProtocol):
    """JobBidResponse

       FIPA-ContractNet Participant Behaviour that runs when an agent
       receives a CFP message. A proposal is sent for a certain job and if it is selected
        (an Accept Propose is received), the job is given to the machine for processing."""

    def __init__(self, agent):
        super(JobBidResponse, self).__init__(agent=agent,
                                             message=None,
                                             is_initiator=False)

    def handle_cfp(self, message):
        """
        """
        self.agent.call_later(1.0, self._handle_cfp, message)

    def _handle_cfp(self, message):
        """
        """
        super(JobBidResponse, self).handle_cfp(message)
        self.message = message

        display_message(self.agent.aid.name, 'CFP message received')
        answer = self.message.create_reply()
        answer.set_performative(ACLMessage.PROPOSE)
        pot_disp = uniform(100, 500)
        answer.set_content(str(pot_disp))
        self.agent.send(answer)

    def handle_reject_propose(self, message):
        """
        """
        super(JobBidResponse, self).handle_reject_propose(message)

        display_message(self.agent.aid.name,
                        'REJECT_PROPOSAL message received')

    def handle_accept_propose(self, message):
        """
        """
        super(JobBidResponse, self).handle_accept_propose(message)

        display_message(self.agent.aid.name,
                        'ACCEPT_PROPOSE message received')

        answer = message.create_reply()
        answer.set_performative(ACLMessage.INFORM)
        answer.set_content('OK')
        self.agent.send(answer)


class TimedJobProposals(TimedBehaviour):
    """TimedJobProposals

        Timed behavbiour that periodically sends out CFPs to Machine Agents in the Job Pool Agents
        workcenter in order to divide jobs amoung the different machines."""

    def __init__(self, agent, notify):
        super(TimedJobProposals, self).__init__(agent, 8.0)
        self.notify = notify
        self.inc = 0

    def on_time(self):
        super(TimedJobProposals, self).on_time()
        message = ACLMessage(ACLMessage.CFP)
        message.set_protocol(ACLMessage.FIPA_CONTRACT_NET_PROTOCOL)
        jobs_to_process = self.agent.subProtocal.get_partial_subscribers("job")
        print('Jobs to process: ' + str(jobs_to_process))
        # content = []
        # for job_agents in jobs_to_process:
        #     content.append(str(job_agents.name))
        # content = jobs_to_process[0].name
        message.set_content('60.0')
        self.notify(message)
        self.inc += 8.0


class TimedJobRelease(TimedBehaviour):
    """Timed protocal for creating new Job Agents within the system"""

    def __init__(self, agent):
        super(TimedJobRelease, self).__init__(agent, 5.0)
        self.inc = 10000

    def on_time(self):
        super(TimedJobRelease, self).on_time()
        job_agent_name = 'job_agent_{}@localhost:{}'.format(self.inc, self.inc)

        job_agent_new = JobAgent(AID(name=job_agent_name), random.randint(1, 6))
        Org.start_single_agent(job_agent_new)
        self.inc += 100


class JobAgent(Agent):
    """Job Agent

        Job agents that contains information regarding the job it represents
        such as processing time, number of operations, current operations, job priority, etc..."""

    def __init__(self, aid, job_type):
        super(JobAgent, self).__init__(aid=aid, debug=False)
        self.call_later(0.5, self.launch_subscriber_protocol)
        self.call_later(6.0, self.stop_agent)
        self.type = job_type

    def launch_subscriber_protocol(self):
        """"
         Request to be subscribed to a certain agent
        """
        msg = ACLMessage(ACLMessage.SUBSCRIBE)
        msg.set_protocol(ACLMessage.FIPA_SUBSCRIBE_PROTOCOL)
        msg.set_content('Subscription request')
        msg.add_receiver(AID('job_pool_agent_20000@localhost:20000'))

        self.protocol = SubscriberProtocolMachine(self, msg)
        self.behaviours.append(self.protocol)
        self.protocol.on_start()

    def stop_agent(self):
        print("Agent Deregistering")
        msg = ACLMessage(ACLMessage.CANCEL)
        msg.set_protocol(ACLMessage.FIPA_SUBSCRIBE_PROTOCOL)
        msg.set_content('Deregister request')
        msg.add_receiver(AID('job_pool_agent_20000@localhost:20000'))

        self.send(msg)
        display_message(self.aid.localname, 'Type of job was: ' + str(self.type))
        Org.deactivate(self)


class MachineAgent(Agent):
    """Machine Agent

        Machine Agent representing a physical machine on the shop floor. It bids on jobs through the CFP
        sent out by the Job Pool Agent in the workcenter it is assigned to.
        It also tracks information regarding the machine"""

    def __init__(self, aid):
        super(MachineAgent, self).__init__(aid=aid, debug=False)
        display_message(self.aid.localname, 'Hello World!')
        self.call_later(4.0, self.launch_subscriber_protocol)
        self.pot_disp = uniform(100.0, 500.0)  # Value to send

        comp = JobBidResponse(self)  # Machine Agents Behaviour

        self.behaviours.append(comp)

    def launch_subscriber_protocol(self):
        """"
         Request to be subscribed to a certain agent
        """
        msg = ACLMessage(ACLMessage.SUBSCRIBE)
        msg.set_protocol(ACLMessage.FIPA_SUBSCRIBE_PROTOCOL)
        msg.set_content('Subscription request')
        msg.add_receiver(AID('job_pool_agent_20000@localhost:20000'))

        self.protocol = SubscriberProtocolMachine(self, msg)
        self.behaviours.append(self.protocol)
        self.protocol.on_start()


class JobPoolAgent(Agent):
    """Job Pool Agent

        Job Pool Agent is a virual agents exisiting within each workcenter on the shop floor.
        It is repsobile for keeping track of jobs that can currently
        be processed within it workcenter by sending out CFPs to machine agents
        registered to the workcenter."""

    def __init__(self, aid):
        super(JobPoolAgent, self).__init__(aid=aid, debug=False)

        self.subProtocal = PublisherProtocolMachine(self)
        self.protocol = JobBidRequest(self)
        self.timedCFP = TimedJobProposals(self, self.protocol.notify)

        self.behaviours.append(self.protocol)
        self.behaviours.append(self.timedCFP)
        self.behaviours.append(self.subProtocal)


class JobReleaseAgent(Agent):
    """Job Release Agent

        Job Release Agent is a singular virual agent that exists on the shop floor
        of the entire factory. It is responsible for the initial release of
        Job Agents (i.e., the virtual representation of Jobs) to the shop floor.
        Currently this is done periodically."""

    def __init__(self, aid):
        super(JobReleaseAgent, self).__init__(aid=aid, debug=False)
        self.behaviours.append(TimedJobRelease(self))


if __name__ == "__main__":
    agents_per_process = 1
    c = 0
    agents = list()
    for i in range(agents_per_process):
        port = int(argv[1]) + c
        print(port)
        k = 1000

        agent_name = 'job_pool_agent_{}@localhost:{}'.format(port, port)
        job_pool_agent_1 = JobPoolAgent(AID(name=agent_name))
        agents.append(job_pool_agent_1)

        agent_name = 'job_release_agent_{}@localhost:{}'.format(port + 1, port + 1)
        job_release_agent_1 = JobReleaseAgent(AID(name=agent_name))
        agents.append(job_release_agent_1)

        for j in range(5):
            agent_name = 'machine_agent_{}@localhost:{}'.format(j + 1, port + 2 + j)
            # participants.append(agent_name)
            agente_part_1 = MachineAgent(AID(name=agent_name))
            agents.append(agente_part_1)

        c += 1000

    Org = Organization(reactor)
    Org.start_loop(agents)
