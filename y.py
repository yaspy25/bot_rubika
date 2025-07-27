import uuid
import json
import asyncio
from warnings import filters
#from rubpy import rubpy.bot.filters
from rubpy.bot.models import Update


bot=BotClient('BFBJB0WYKBSPUEWEVFGQEXURBYEGYLGXCGBMXRIPUEFHBPEQJGVWNYWLDMEZATRW')
exam_data={}
exam_file='exams.json'

def load_exams():
    try: 
        with open(exam_file,'r',encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return{}


def save_exams(data):
    with open(exam_file,'w',encoding='utf-8') as f:
        json.dump(data,f,ensure_ascii=False,indent=2)


@bot.on_update()
async def create_exam(c: BotClient, update: Update):
    if update.new_message and update.new_message.text == "/create_exam":
        exam_data[update.chat_id] = {
            'step': 'ask_title',
            'title': '',
            'duration': 0,
            'questions': []
        }
        await c.send_message(chat_id=update.chat_id, text='📝 عنوان آزمون را وارد کنید:')
@bot.on_update()
async def handle_exam_steps(c:BotClient,update:Update):
    if update.new_message and update.chat_id in exam_data:
        exam=exam_data[update.chat_id]
        msg=update.new_message.text.strip()
        if exam['step']=='ask_title':
            exam['title']=msg
            exam['step']='ask_duraton'
            await update.reply('مدت ازمون را وارد کنید: ')
        elif exam['step']=='ask_duraton':
            if msg.isdigit():
                exam['duration']=int(msg)
                exam['step']='ask_question'
                await update.reply('سوال را وارد کنید :')
            else:
                await update.reply('لطفا فقط عدد وارد کنید')
        elif exam['step']=='ask_question':
            exam['current_question']={"text":msg,'choices':[]}
            exam['step']='ask_choice_0'
            await update.reply('گزینه 1 را وارد کنید: ')

        elif exam['step'].startswith('ask_choice_'):
            index=int(exam['step'][-1])
            exam['current_question']['choices'].append(msg)
            if index<4:
                exam['step']=f'ask_choice_{index+1}'
                await update.reply('گزینه {index+2}را وارد کنید :  ')
            else:
                exam['step']='ask_answer'
                await update.reply("گزینه درست را وارد کنید:")
        elif exam['step']=='ask_answer':
            if msg in ['1','2','3','4','5']:
                answer_index=int(msg)-1
                exam['current_question']['answer']=answer_index
                exam ['questions'].append(exam['current_question'])
                del exam['current_question']
                exam['step']='ask_next'
                #اماده برای سوال بعدی یا پایان
                await update.reply('سوال دیگری دارید ؟ بله / خیر ')
            else: 
                await update.reply('لطفا عددی بین 1تا 5 وارد کنید ')
        elif exam['step']=='ask_next':
            if msg.lower()in['بله','خیر','no']:
                all_exams=load_exams()
                exam_id=f'exam_{uuid.uuid4().hex[:6]}'
                all_exams[exam_id]={'owner_id':update.new_message.sender_id,'title':exam['title'],'duration':exam['duration'],'questions':exam['questions']}
                save_exams(all_exams)
                await update.reply(f'ازمون با موفقیت ذخیره شد! \n ایدی ازمون:{exam_id}')
                del exam_data[update.chat_id]
            else:
                await update.reply('لطفا فقط بله یا خیر وارد کنید')
asyncio.run(bot.run())


#بارگذاری نتایج از فایل
def load_results():
    try: 
        with open('results.json','r') as f:
          return json.load(f)
    except FileNotFoundError:
        return{}
#ذخیره نتایج در فابل 
def save_results(results):
    with open('results.json','w') as f:
        json.dump(results,f,indent=2)


@bot.on_message(filters.command('join_exam'))  
async def join_exam(client,message):
    await message.reply('نام ونام خانوادگی خود را وارد کنید: ')
    name_msg=await bot.listen(message.chat.id)
    await message.reply('سن خودرا وارد کنید:')
    age_msg=await bot.listen(message.chat.id)
    await message.reply("ایدی روبیکای خود را وارد کنید:")
    id_msg=await bot.listen(message.chat.id)
    await message.reply('لطفا کد ازمون را وارد کنید:')
    exam_id_msg=await bot.listen(message.chat.id)

    exam_id=exam_id_msg.text.strip()
    exams=load_exams()

    if exam_id not in exams:
        await message.reply('ازمونی با این کد یافت نشد')
        return
    exam=exams[exam_id]
    score=0
    wrong_answers=[]
    user_answers=[]

    for i,q in enumerate(exam['questions']):
        text=f'سوال{i+1}:{q["text"]}\n'
        for idx,option in enumerate(q['options']):
            text+=f'{idx+1}.{option}\n'
        await message.reply(text)
        #انتظار پاسخ با تایمر 60سانیه 
    try:
        answer_msg= await bot.listen(message.chat.id,TimeoutError=60)
        user_answer=int(answer_msg.text.strip())-1
    except:
        user_answer=-1  # بی پاسخ 
        user_answer.append(user_answer)

    if user_answer==q['answer']:
        score+=1
    else:
        wrong_answers.append({'number':i+1,'question':q["text"],
                         'your_answer':user_answer,
                         'correct_answer':q["answer"],
                         'explanation':q['explanation']})
    total_questions=len(exam['questions'])
    percent=round(score/total_questions*100,2)
    #ذخیره نتیجه در فایل
    results=load_results()
    if exam_id not in results:
        results[exam_id]=[]
        results[exam_id].append({'name':name_msg.text,
                                'age':age_msg.text,
                                'id':id_msg.text,
                                'score':score,
                                'total':total_questions,
                                'percent':percent,
                                'wrong':wrong_answers})
    save_results(results)

    #نمایش نتیجه به ازمون دهنده
    result_text=f'ازمون به پایان رسید!\n نمره شما:{score}{total_questions}({percent}%) \n '
    if wrong_answers:
        result_text+='\n سوالات اشتباه: \n'
        for wa in wrong_answers:
            result_text+=f'\nسوال \n {wa["number"]}:\n {wa["question"]}\n'
            result_text+=f'پاسخ شما : {wa["your_answer"]+1 if wa["your_answer"]!=-1 else "بی پاسخ"} \n '
            result_text+=f'پاسخ صحیح :{wa["correct_answer"]+1} \n '
            result_text+=f'پاسخ تشریحی:{wa["explanation"]} \n '
    await message.reply(result_text)



@bot.on_update(CommandFilter('my_exams'))
async def list_my_exams(c:BotClient,update:Update):
    all_exams=load_exams()
    owner_id=update.new_message.sender_id
    exams_list=[eid for eid , exam in all_exams.items()if exam['owner_id'==owner_id]]

    if not exams_list:
        await update.reply('شما هنوز ازمونی نساختید!')
        return

    text='لیست ازمون های شما:\n'
    for eid in exams_list:
        exam=all_exams[eid]
        text+=f'\n-{exam["title"]}(کد:{eid})'
    text+='\n\n کد ازمون مورد نظر را ارسال کنید تا نتایج ان نمایش داده شود'
    users[update.chat_id]={'step':'waiting_exam_code'}
    await update.reply(text)

@bot.on_update()
async def handle_exam_code_for_results(c:BotClient,update:Update):
    if not update.new_message:
        return
    chat_id=update.chat_id
    msg=update.new_message.text.strip()
    if chat_id not in users or users[chat_id].get('step')!='waiting_exam_code':
        return
    all_exams=load_exams()
    results_data=load_results()
    if msg not in all_exams:
        await update.reply("کد معتبر نیست.")
    exam=all_exams[msg]
    owner_id=update.new_message.sender_id
    if exam['owner_id']!=owner_id: 
        await update.reply('شما مالک این ازمون نیستید')
    if msg == (not results_data or not results_data[msg]):
        await update.reply('هنوز هیچ کاربری شرکت نکرده است!')
        return 
    text=f'نتایج ازمون <<{exam["title"]}>>:\n'
    for i,participant in enumerate(results_data[msg]):
        text+=f'\n {i+1}.{participant["name"]}-نمره:{participant["score"]} {participant["total"]}({participant["percent"]}%)'
    text+='\n\n برای جستجو نتیجه یک شرکت کننده نام کامل او را ارسال کنید.\nبرای خروج هر پیام دیگری ارسال کنید . '
    users[chat_id]['step']=f'search_{msg}'
    await update.reply(text)
@bot.on_update()
async def search_participant_by_name(c:BotClient,update:Update):
    if not update.new_message:
        return
    chat_id=update.chat_id
    msg=update.new_message.text.strip()
    step=users.get(chat_id,{}).get('step',"")

    if not step.startswith('search_'):
        return
    exam_id=step[7:]
    result_data=load_results()
    all_exams=load_exams()
    exam=all_exams.get(exam_id)


    if not exam :
        await update.reply('ازمون پیدا نشد.')
        users[chat_id]['step']=None
        return

    #جستجو بین شرکت کنندگان
    participants=result_data.get(exam_id,[])
    found=None
    for p in participants:
        if p['name']==msg:
            found=p
            break

    if not found:
        await update.reply('شرکت کننده ای با این نام یافت نشد.')
        return
    #نمایش جزئیات شرکت کننده
    text=(f'نام:{found["name"]}\n'
          f'سن:{found["age"]}\n'
          f'ایدی روبیکا:{found["id"]}\n'
          f'نمره:{found["score"]}/{found["total"]}({found["percent"]}%)\n')
    if found['wrong']:
        for wa in found['wrong']:
            your_ans=wa['your_answer']+1 if wa['your_answer']!=-1 else 'بی پاسخ'
            correct_ans= wa['correct_answer']+1
            text+=(f'\n سوال{wa["number"]}:\n'
                   f"{wa['question']}\n"
                   f'پاسخ شما:{your_ans}\n'
                   f'پاسخ درست:{correct_ans}\n'
                   f"پاسخ  تشریحی:{wa['explanation']}\n")
    else:
        text+= 'هیچ سوال اشتباهی وجود ندارد '

    await update.reply(text)


@bot.on_update(CommandFilter('edit_exam '))
async def edit_exam_start(c:BotClient,update:Update):
    all_exams=load_exams()
    owner_id=update.new_message.sender_id
    exams_list=[eid for eid ,exam in all_exams.items() if exam['owner_id']==owner_id]

    if not exams_list:
        await update.reply('شما هنوز ازمونی نساخته اید.')
        return
    text='لیست ازمون های شما برای ویرایش:\n'
    for eid in exams_list:
        exam=all_exams[eid]
        text+=f' n-{exam["title"]}(کد:{eid})'
        text+='\n \n کد ازمون را وارد کنید:'
        users[update.chat_id]={'step':'edit_waiting_exam_code'}
        await update.reply(text)
@bot.on_update()
async def handle_edit_exam(c:BotClient,update:Update):
    await update.new_message.text.strip()
    if chat_id not in users:
        return
    step=users[chat_id].get('step')
    all_exams=load_exams()


    #انتخاب ازمون برای ویرایش 
    if step=='edit_waiting_exam_code':
        if msg not in all_exams:
            await update.reply('کد ازمون معتبر نیست')
            return
        exam = all_exams[msg]
        owner_id =update.new_message.sender_id
        if exam['owner_id'] !=owner_id:
            await update.reply('شما مالک این ازمون نیستید.')
            return
        users[chat_id]['step']='editing_exam'
        users[chat_id]['editing_exam_id']=msg
        await update.reply('ازمون انتخاب شد .\nبرای مشاهده سوالات "نمایش " را ارسال کنید .\n  برای افزودن سوال جدید "اضافه" را ارسال کنید \nبرای حذف سوال "حذف شماره" و \n برای ویرایش سوال "ویرایش شماره " را ارسال کنید.')
        #در پنل ویرایش ازمون 
    elif step=='editing_exam':
        exam_id=users[chat_id]['editing_exam_id']
        exam=all_exams[exam_id]

        if msg=="نمایش":
            if not exam['questions']:
                await update.reply('این ازمون سوالی ندارد.')
                return
        text='سوالات ازمون :\n'
        for i,q in enumerate(exam['questions'],1):
            text +=f'\n{i}.{q["text"]}'
        await update.reply(text)
        if msg=='حذف ':
            try:
                num=int(msg.split('')[1])
                if 1<=num<=len(exam['questions']):
                    removed=exam['questions'].pop(num-1)
                    save_exams(all_exams)
                    await update.reply(f'سوال شماره {num} حذف شد:\n{removed["text"]}')
            except:
                await update.reply('فرمت دستور حذف صحیح نیست مانند :حذف 2')
            else:
                await update.reply('شماره سوال نامعتبر است.')
        elif msg=='ویرایش':
            try:
                num=int(msg.split('')[1])
                if 1<=num<=len(exam['questions']):
                    users[chat_id]['step']='editing_question'
                    users[chat_id['question_num']]=num-1
                    await update.reply('متن جدید سوال را وارد کنید:')

                else:
                    await update.reply('شماره سوال نامعتبر است')

            except:
                await update.reply('فرمت دستور ویرایش صحیح نیست.مانند:ویرایش3')

        elif msg=='اضافه':
            users[chat_id]['step']='adding_question'
            await update.reply('سوال جدید را وارد کنید:')
        else:
            await update.reply('دستور نامعتبر است.\n از دستورات :نمایش /اضافه/حذف شماره/ویرایش شماره استفاده کنید.')

    # ویرایش متن سوال  
    elif step=='editing_question':
        exam_id=users[chat_id]['editing_exam_id']
        num=users[chat_id]['question_num']
        exam=all_exams[exam_id]
        exam['question'][num]['text']=msg
        save_exams(all_exams)
        users[chat_id]['step']='editing_question_choices'
        await update.reply('گزبنه 1 را وارد کنید')
    #ویرایش گزینه ها 
    elif step=='editing_choices':
        exam_id=users[chat_id]['editing_exam_id']
        num=users[chat_id]['question_num']
        exam=all_exams[exam_id]
        question=exam['questions'][num]

        if 'edit_choices' not in users[chat_id]:
            users[chat_id]['edit_choices']=[]
        users[chat_id]['edit_choices'].append(msg)

        if len(users[chat_id]['edit_choices'])<5:
            await update.reply(f'گزینه {len(users[chat_id]["edit_choices"])+1}را وارد کنید:')

        else:
            question['choices']=users[chat_id]['edit_choices']
            users[chat_id]['edit_choices']=[]
            users[chat_id]['step']='editing_question_answer'
            await update.reply('شماره گزینه درست را وارد کنید(1تا5):')

    #ویرایش پاسخ صحیح 
    elif step=='editing_question_answer':
        if msg in ['1','2','3','4','5']:
            exam_id=users[chat_id]['editing_exam_id']
            num=users[chat_id]['question_num']
            exam=all_exams[exam_id]
            question['answer']=int(msg)-1
            save_exams(all_exams)
            users[chat_id]['step']='editing_exam'
            await update.reply('سوال با موفقیت ویرایش شد.')
        else:
            await update.reply('لطفا عددی بین 1 تا 5 وارد کنید')

    #اضافه کردن سوال جدید 
    elif step=='adding_question':
        users[chat_id]['new_question']={'text':msg,'choices':[]}
        users[chat_id]['step']='adding_question_choices'
        await update.reply('گزینه 1 را وارد کنید:')


    elif step =='adding_question_choices':
        if 'new_question' not in users[vhat_id]:
            await update.reply('خطا در داده ها دوباره /edit_exam را بزنید.')
            users[chat_id]['step']=None
            return
        users[chat_id]['new_question']['choices'].append(msg)

        if len(users[chat_id]['new_question']['choices'])<5:
            await update.reply(f'گزینه {len(users[chat_id]["new_question"]["choices"])+1}را وارد کنید:')

        else:
            users[chat_id]['step']='adding_question_answer'
            await update.reply('شماره گزینه صحیح را وارد کنید:(1تا 5)')


    elif step=='adding_question_answer':
        if msg in ['1','2','3','4','5']:
            new_q=users[chat_id]['new_question']
            new_q['answer']=int(msg)-1
            exam_id=users[chat_id]['editing_exam_id']
            all_exams=load_exams()
            all_exams[exam_id]['questions'].append(new_q)
            save_exams(all_exams)
            users[chat_id]['step']='editing_exam'
            del users[chat_id]['new_question']
            await update.reply('سوال جدید با موفقیت اضافه شد.')
        else:
            await update.reply('لطفا عددی بین 1 تا 5 وارد کنید.')

#مدیریت
ADMINS=['@Yasin0685']
@bot.on_message(filters.text)
async def handle_message(client,update):
    user_id=message.user.username

    if message.text=="پنل مدیریت" and user_id in ADMINS:
        await show_admin_panel(message)

async def show_admin_panel(message):
    users=load_json('users.json')
    exams=load_json('exams.json')

    num_users=len(users)
    num_exams=len(exams)

    top_exam=None
    max_participants=0
    for exam_code,exam in exams.items():
        participants=len(exam.get('participants',[]))
        if participants>max_participants:
            max_participants=participants
            top_exam=exam.get('title','بدون عنوان')

    text=f"پنل مدیریت:\n تعداد کل کاربران:{num_users} \n تعداد کل ازمون ها:{num_users} \n پرمخاطب ترین آزمون :({max_participants}شرکت کننده) \n لیست آزمون ها :{top_exam}"
    for code,exam in exams.items():
        count=len(exam.get('participants'),[])
        text+=f"\n {exam.get('title','نامشخص')}-{count}نفر "

    await message.reply(text)

















