import json 
import pdb 
import argparse 

parser = argparse.ArgumentParser()
parser.add_argument('--generate', action='store_true', default=False)
args = parser.parse_args()

results = []
# 读取mbti_results.jsonl文件，里面每行是一个json，包含了id，question，response_open，response_closed四个字段，其中response_open是开放式回答，response_closed是闭合式回答。
with open('mbti_results.jsonl', encoding='utf-8') as f:
    for line in f:
        data = json.loads(line)
        results.append(data)

# mbti_results.jsonl里忘了存character_name了..只能按idx划分了
NAME_DICT = {'汤师爷': 'tangshiye', '慕容复': 'murongfu', '李云龙': 'liyunlong', 'Luna': 'Luna', '王多鱼': 'wangduoyu',
             'Ron': 'Ron', '鸠摩智': 'jiumozhi', 'Snape': 'Snape',
             '凉宫春日': 'haruhi', 'Malfoy': 'Malfoy', '虚竹': 'xuzhu', '萧峰': 'xiaofeng', '段誉': 'duanyu',
             'Hermione': 'Hermione', 'Dumbledore': 'Dumbledore', '王语嫣': 'wangyuyan',
             'Harry': 'Harry', 'McGonagall': 'McGonagall', '白展堂': 'baizhantang', '佟湘玉': 'tongxiangyu',
             '郭芙蓉': 'guofurong', '旅行者': 'wanderer', '钟离': 'zhongli',
             '胡桃': 'hutao', 'Sheldon': 'Sheldon', 'Raj': 'Raj', 'Penny': 'Penny', '韦小宝': 'weixiaobao',
             '乔峰': 'qiaofeng', '神里绫华': 'ayaka', '雷电将军': 'raidenShogun', '于谦': 'yuqian'}

character_names = list(NAME_DICT.keys())
character_responses = {name:[] for name in character_names}

# 将results按照角色划分
for idx, data in enumerate(results):
    cname = character_names[ idx // 60 ]
    character_responses[cname].append(data)
    

# 观察每个角色的results条数是否等于60
#for name in character_names:
#    print(name, len(character_responses[name]))
    
save_name = 'mbti_results_open.jsonl' 
# 开放式测试 - 通过GPT-4评价
dims = ['E/I', 'S/N', 'T/F', 'P/J']

if args.generate:
    open_prompt_template = '''You are an expert in MBTI. I am conducting an MBTI test on someone. My goal is to gauge their position on the {} spectrum of the MBTI through a series of open-ended questions. For clarity, here's some background on differentiating this particular dimension:
    ===
    {}
    ===

    I've invited a participant, {}, and had the following conversations in Chinese:
    ===
    {}
    ===

    Please help me distinguish whether {} leans more towards the {} or {} category within the MBTI's {} dimension. Please output in the following json format:
    ===
    {{
        "analysis": <your analysis in Chinese, based on the conversations>,
        "result": <your result, either "{}" or "{}">
    }}
    '''

    open_dimension_prompt = {
        'E/I': '''E/I Dimension: Extraversion (E) vs Introversion (I)

    E (Extraversion): Extraverts draw energy from interacting with others. They feel comfortable in social settings and tend to express their thoughts. Extraverts are often more active, seek social stimulation, and enjoy participating in group activities. For them, connecting with people, sharing, and exchanging ideas is often a need. They might be more focused on external world stimuli, such as sounds, colors, and social dynamics.

    I (Introversion): Introverts feel more comfortable when alone. They derive energy from inner reflection and personal time. Contrary to extraverts, prolonged social interaction might tire them. Introverts might be more introspective, enjoy deep thinking, and tend to have meaningful personal relationships. They are more concerned with the inner world, such as thoughts, emotions, and imaginations.''',

        'S/N': '''S/N Dimension: Sensing (S) vs Intuition (N)

    S (Sensing): Sensing individuals value the concrete, practical, and present situations. They rely on their five senses to process information and often focus on details. For them, past experiences and tangible evidence play a significant role in decision-making. They are typically pragmatic and tend to deal with what they "see" and "hear".

    N (Intuition): Intuitive individuals tend to focus on potential possibilities and future opportunities. They like to think about "what could be", rather than just "what is". They lean more towards abstract thinking and can capture concepts and patterns effectively. Intuitives are often more innovative, preferring new ideas and approaches.''',

        'T/F': '''T/F Dimension: Thinking (T) vs Feeling (F)

    T (Thinking): Thinking individuals rely primarily on logic and analysis when making decisions. They pursue fairness and objectivity and might be more direct and frank. For them, finding the most efficient method or the most logical solution is crucial, even if it might hurt some people's feelings.

    F (Feeling): Feeling individuals consider people's emotions and needs more when making decisions. They strive for harmony, tend to build relationships, and avoid conflicts. They are often more empathetic, valuing personal values and emotions, rather than just facts or logic.''',

        'P/J': '''P/J Dimension: Perceiving (P) vs Judging (J)

    P (Perceiving): Perceivers are more open and flexible. They tend to "go with the flow" rather than overly planning or organizing things. Perceivers like to explore various possibilities and prefer to leave options open to address unforeseen circumstances. They lean towards postponing decisions to gather more information and better understanding. For them, life is a continuous process of change, not an event with fixed goals or plans. They often focus more on the experience itself rather than just the outcome.

    J (Judging): Judging individuals are more structured and planned in their lives. They prefer clear expectations and structures and often set goals and pursue them. Judgers are usually more organized and tend to make decisions in advance. They like to act according to plans and feel comfortable in an orderly environment. For them, achieving goals and completing tasks are often priorities. They might focus more on efficiency and structure rather than openness or spontaneity.'''
    }

    from utils import get_response 

    open_results = {name:{'character': name} for name in character_names}

    for cname in character_names:
        responses = character_responses[cname]

        # 每个角色应该包含60个问题
        assert( len([r for r in responses if r['factor'] in dims]) == 60 )

        test_role = responses[0]['test_role']

        

        for dim in dims:
            dim_responses = [r for r in responses if r['factor'] == dim]

            conversations = ''
            for i, r in enumerate(dim_responses):
                # 问题
                conversations += f'{i+1}.\n'
                conversations += f"{test_role}: 「{r['question']}」\n"
                # 答案
                if not r['response_open'].startswith(cname):
                    r['response_open'] = cname + ': 「' + r['response_open'] + '」'
                conversations += f"{r['response_open']}\n"
            
            t1, t2 = dim.split('/')
            # 生成prompt

            prompt = open_prompt_template.format(dim, open_dimension_prompt[dim], cname, conversations, cname, t1, t2, dim, t1, t2)

            sys_prompt, user_input = prompt.split("I've invited a participant")
            user_input = "I've invited a participant" + user_input

            llm_response = get_response(sys_prompt, user_input, model="gpt-4")
            # 将llm_response转为json
            llm_response = json.loads(llm_response)

            open_results[cname][dim] = llm_response

        
        with open(save_name, 'a', encoding= 'utf-8') as f:
            json.dump(open_results[cname], f, ensure_ascii=False)
            f.write('\n')

# 读取标签
labels = {}
with open('mbti_labels.jsonl', encoding='utf-8') as f:
    for line in f:
        data = json.loads(line)
        labels[data['character']] = data['label']

# 读取open_results
open_results = {}
with open('mbti_results_open.jsonl', encoding='utf-8') as f:
    for line in f:
        data = json.loads(line)
        open_results[data['character']] = data

# single: 单一维度评价；full：全维度评价
count_single = 0
right_single = 0 
count_full = 0
right_full = 0

possible_chars = set(['E', 'I', 'S', 'N', 'T', 'F', 'P', 'J', 'X'])

for cname, gts in labels.items():
    # 预测结果
    pds = [open_results[cname][dim]['result'] for dim in dims]
    # groundtruth
    gts = [_ for _ in gts]

    print('Character {}\t\tResults {}\tLabels {}'.format(cname, ''.join(pds), ''.join(gts)))

    full_sign = True 

    for pd, gt in zip(pds, gts):
        assert(pd in possible_chars and gt in possible_chars)
        if gt == 'X':
            continue 
        else:
            if gt == pd:
                right_single += 1
            else:
                full_sign = False
            count_single += 1

    if full_sign: 
        right_full += 1
    count_full += 1

print('单一维度评价：Count: {}\tRight: {}\tAcc: {:.4f}'.format(count_single, right_single, right_single/count_single))
print('全部维度评价：Count: {}\tRight: {}\tAcc: {:.4f}'.format(count_full, right_full, right_full/count_full))    





