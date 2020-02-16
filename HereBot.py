import vk_api
import random
import logging
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType

WELCOME_MSG = 'Бот создан Профкомом ВМК МГУ. Автор - Журихин Юрий\n' \
              'Чтобы начать использование - добавьте меня в беседу и выдайте права администратора\n' \
              '@channel - упоминает всех людей в беседе\n' \
              '@here - упоминает тех, кто online\nv2.1'


class VkBot:
    def __init__(self):
        logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(funcName)s - %(message)s')
        logging.info('Connecting...')
        self.token = 'b61977fd0b6bba38c20499bb2f0ac170db03130740645a1dd9eded9916e5c46e593ada03ec1876c801561'
        self.group_id = '187762497'
        self.vk_session = vk_api.VkApi(token=self.token)
        self.vk = self.vk_session.get_api()
        self.PACK_SIZE = 50  # Size for users to ping in one message
        logging.info('Connected!')

    def get_long_poll(self):
        return VkBotLongPoll(self.vk_session, group_id=self.group_id)

    def send_message(self, peer_id, text):
        self.vk.messages.send(
            random_id=random.randint(0, 1 << 31),
            peer_id=peer_id,
            message=text,
        )

    def get_conversation_members(self, peer_id):
        ans = self.vk.messages.getConversationMembers(peer_id=peer_id)
        try:
            return ans['profiles']
        except:
            logging.error("Can't get conversation members")

    def message_handler(self, event):
        text = event.obj.text
        peer_id = event.obj.peer_id
        from_id = event.obj.from_id
        if event.from_user:
            logging.info('welcome to vk.com/id{}'.format(from_id))
            self.send_message(peer_id, WELCOME_MSG)
        elif event.from_chat:
            try:
                if '@channel' in text:
                    logging.info('channel from vk.com/id{}'.format(from_id))
                    self.channel(peer_id, text, event.obj.from_id)
                elif '@here' in text:
                    logging.info('here from vk.com/id{}'.format(from_id))
                    self.here(peer_id, text, event.obj.from_id)
                elif '@vote' in text:
                    logging.info('vote from vk.com/id{}'.format(from_id))
                    self.vote(event.obj)
                elif '/ping' in text:
                    logging.info('ping from vk.com/id{}'.format(from_id))
                    self.send_message(peer_id, 'pong')
            except vk_api.exceptions.ApiError as e:
                logging.error(str(e))

    def channel(self, peer_id, text, from_id):
        if '[id457265466|@channel]' in text:
            useful = ''.join(text.split('[id457265466|@channel]'))
        elif '[id3696360|@channel]' in text:
            useful = ''.join(text.split('[id3696360|@channel]'))
        else:
            useful = ''.join(text.split('@channel'))
        profiles = self.get_conversation_members(peer_id)
        text = []
        for profile in profiles:
            if 'deactivated' in profile.keys():
                logging.info('deactivated catched!')
                continue
            try:
                if profile['id'] == from_id:
                    continue
                text.append('@' + profile['screen_name'] + ' (_)')
            except KeyError:
                logging.error('Key Error')
                logging.error(profile)
        self.send_message(peer_id, useful + '\n' + ''.join(text[:self.PACK_SIZE]))
        for i in range(1, len(text) // self.PACK_SIZE + 1):
            self.send_message(peer_id, ''.join(text[i * self.PACK_SIZE:(i + 1) * self.PACK_SIZE]))

    def here(self, peer_id, text, from_id):
        if '[id457265466|@here]' in text:
            useful = ''.join(text.split('[id457265466|@here]'))
        else:
            useful = ''.join(text.split('@here'))
        profiles = self.get_conversation_members(peer_id)
        text = []
        for profile in profiles:
            if profile['online'] == 1 and profile['id'] != from_id:
                text.append('@' + profile['screen_name'] + ' (_)')
        self.send_message(peer_id, useful + '\n' + ''.join(text))

    def vote(self, message):
        profiles = self.get_conversation_members(message.peer_id)
        poll = None
        for fwd in message.fwd_messages:
            if poll is not None:
                break
            if fwd['attachments'] is not None:
                for att in fwd['attachments']:
                    if att['type'] == 'poll':
                        poll = att['poll']
                        break
        if poll is None:
            logging.error("Can't find poll in the message: \n{}\nfrom: vk.vom/id{}".format(message, message.from_id))
            return
        answers = [ans['id'] for ans in poll['answers']]
        voters = self.vk.polls.getVoters(owner_id=poll['owner_id'], poll_id=poll['id'], answer_ids=answers)
        users = set()
        for ans in voters:
            for usr in ans['users']:
                users.add(usr['id'])
        print(users)

    def start(self):
        logging.info('Starting...')
        longpoll = self.get_long_poll()
        try:
            for event in longpoll.listen():
                if event.type == VkBotEventType.MESSAGE_NEW:
                    self.message_handler(event)
        except KeyboardInterrupt:
            logging.info('Stopping...')


bot = VkBot()
bot.start()
