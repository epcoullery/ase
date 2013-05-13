# -*- coding: utf-8 -*-
import json
#import locale
import math
from datetime import date
import csv, codecs, cStringIO
from django.shortcuts import render, get_object_or_404
from django.template import RequestContext
from django.db.models import Sum
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.dateformat import format
from django.core.servers.basehttp import FileWrapper
from reportlab.platypus import Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle as PS
from reportlab.lib.enums import TA_CENTER, TA_LEFT,TA_RIGHT,TA_JUSTIFY

from models import (Promotion, AppliedStudiesPlan, TheoricStudiesPlan, Teacher,
    Content, AdminJob, MyDocTemplate, Supervision, Todo)


def teachers(request, pk):
    """
    Le paramètre est optionnel. S'il est absent, la première valeur
    de la table est utilisée.
    """
    data = {}
    teachers = Teacher.objects.all()
    if pk is None:
        teacher_selected = teachers[0]
    else:
        teacher_selected = get_object_or_404(Teacher, pk=pk)
    data['teachers'] = teachers
    data['teacher_selected'] = teacher_selected
    data['courses'] = AppliedStudiesPlan.objects.filter(teacher_id=teacher_selected.id)
    data['student_total'] = data['courses'].aggregate(Sum('student_period'))['student_period__sum']
    data['teacher_total'] = data['courses'].aggregate(Sum('teacher_period'))['teacher_period__sum']
    data['missions']=AdminJob.objects.filter(teacher_id = teacher_selected.id)
    return render(request, 'teachers.html', data)


def promotions(request, pk):
    """
    Le paramètre est optionnel. S'il est absent, la première valeur
    de la table est utilisée.
    """
    data ={}
    data['promotions'] = Promotion.objects.all()
    if pk is None:
        promotion_selected = data['promotions'][0]
    else:
        promotion_selected = get_object_or_404(Promotion, pk=pk)
    data['teachers'] = Teacher.objects.all()
    data['promotion_selected'] = promotion_selected
    data['courses'] = AppliedStudiesPlan.objects.filter(promotion_id = promotion_selected.id)
    data['student_total'] = data['courses'].aggregate(Sum('student_period'))['student_period__sum']
    data['teacher_total'] = data['courses'].aggregate(Sum('teacher_period'))['teacher_period__sum']
    return render(request, 'promotions.html', data)


def contents(request,pk):
    """
    Le paramètre est optionnel. S'il est absent, la première valeur
    de la table est utilisée.
    """
    data = {}
    if pk is None:
        content_selected = Content.objects.all()[0]
    else:
        content_selected = get_object_or_404(Content,pk=pk)
    contents = Content.objects.all()
    #contents.query.group_by=['code']
    teachers = Teacher.objects.all()
    data['contents'] = contents
    data['teachers'] = teachers
    data['content_selected'] = content_selected
    data['courses'] = AppliedStudiesPlan.objects.filter(content__code = content_selected.code)
    data['student_total'] = data['courses'].aggregate(Sum('student_period'))['student_period__sum']
    data['teacher_total'] = data['courses'].aggregate(Sum('teacher_period'))['teacher_period__sum']
    return render(request, 'contents.html', data)


def missions(request):
    missions=AppliedStudiesPlan.objects.filter(promotion__name='Mandat')
    return render(request, 'missions.html', {'missions':missions})

def teachers_charges(request, pk):
    """
    Impression de la feuille de charge au format PDF
    """
    if request.method == 'POST':
        teacher = get_object_or_404(Teacher, pk=pk)
        response = HttpResponse(mimetype='application/pdf')
        response['Content-Disposition'] = 'attachment; filename=somefilename.pdf'
        style_normal = PS(name = 'CORPS', fontName='Helvetica', fontSize=10, alignment = TA_LEFT)
        style_bold = PS(name = 'CORPS', fontName='Helvetica-Bold', fontSize=10, alignment = TA_LEFT)
        style_adress = PS(name = 'CORPS', fontName='Helvetica', fontSize=10, alignment = TA_LEFT, leftIndent=300)

        missions = AdminJob.objects.filter(teacher_id=teacher.id)
        story=[]
        story.append(Paragraph(u"Ecole Pierre-Coullery", style_normal))
        story.append(Paragraph(u"2300 La Chaux-de-Fonds", style_normal))
        story.append(Spacer(1, 3*cm))
        story.append(Paragraph(teacher.full_name(), style_adress))
        story.append(Spacer(1, 3*cm))
        story.append(Paragraph(u'La Chaux-de-Fonds, le ' + format(date.today(), 'd F Y'), style_normal))
        story.append(Spacer(1, 3*cm))
        story.append(Paragraph(u'Charge d\'enseignement pour l\'année scolaire 2013-2014', style_bold))
        story.append(Spacer(1, 0.5*cm))
        total = teacher.total()
        if teacher.extern == False:
            tab = [[u'Transmission des savoirs (coef. 2, liste des cours en annexe)', u'%d pér.' % (total['teaching'])]]
            tab.append([u'Mandats particuliers', u'%d pér.' % total['mission']])
            tab.append([u'    -%s ( %d pér.)' % (u'Colloques pédagogiques', 24),''])
            for mission in missions:
                libel = u'    -%s ( %d pér.)' % (mission.content.name, mission.teacher_period)
                tab.append([libel, ''])
            tot_super = Supervision.objects.filter(teacher_id=teacher.id).aggregate(Sum('teacher_period'))['teacher_period__sum']
            if tot_super is None:
                tot_super = 0
            tab.append([u'Suivis expérientiels (FE + MP)', u'%d pér.' % (tot_super)])
            tab.append([u'Autres tâches', u'%d pér.' % (total['others'])])
            tab.append([u'Total', u'%d pér.' % (total['total']), u'%.1f EPT' % (total['ept']/100)])
        else:
            tab = [[u'Transmission des savoirs (coef. 1 - !!!Externe!!!, liste des cours en annexe)', u'%d pér.' % (total['teaching']/2)]]    
            tab.append([u'Total', u'%d pér.' % (total['total']/2), u'%.1f EPT' % (total['ept']/100/2)])

        t = Table(tab, repeatRows=1)
        t.setStyle(TableStyle([('LEADING',   (0,1), (-1,-1), 8),
                               ('ALIGNMENT', (1,0), ( 1,-1), 'RIGHT')]))
        story.append(t)
        #Signature
        story.append(Spacer(1, 5*cm))
        story.append(Paragraph(u'la direction', style_normal))

        #Saut de page pour liste des cours
        story.append(PageBreak())
        story.append(Spacer(1, 1*cm))
        story.append(Paragraph(u'Liste des cours:', style_bold))
        story.append(Spacer(1, 0.5*cm))
        tab = [['Classes', 'Cours', 'Périodes']]
        courses = AppliedStudiesPlan.objects.filter(teacher_id=teacher.id).order_by('promotion__name','content__name')
        for c in courses:
            tab.append([c.promotion.name, c.content.code + " : " + c.content.name, c.teacher_period])
        #Ajoute le total
        tab.append(['','Total :', '%d' % (total['teaching']/2)])

        t = Table(tab, repeatRows=1)
        t.setStyle(TableStyle([('LEADING',   (0,1), (-1,-1), 8),
                               ('ALIGNMENT', (2,1), ( 2,-1), 'RIGHT'),
                               ('LINEABOVE', (0,1), (-1,1), 1, colors.black),]))
        story.append(t)

        doc = MyDocTemplate(response, teacher)
        doc.build(story)
        return response




def generate(request):
    """
    Génère le cpurs de la classe passée en paramètre
    """
    if request.method == 'POST':
        if 'promotion_to_generate' in request.POST:
            #promotion_name = request.POST['promotion_to_generate']
            promotion = Promotion.objects.get(name=request.POST['promotion_to_generate'])
            pt = TheoricStudiesPlan.objects.filter(formation_id = promotion.formation_id)
            #Efface les cours déjà enregistrer
            AppliedStudiesPlan.objects.filter(promotion_id=promotion.id).delete()
            for p in pt:
                AppliedStudiesPlan(promotion_id = promotion.id,
                                   content_id = p.content_id,
                                   teacher_id = None,
                                   teacher_period = p.teacher_period,
                                   student_period = p.student_period).save()
    return HttpResponseRedirect('/promotions')


def genall(request):
    """
    Génère tous les cours appliqués
    Afin d'éviter toute erreur de manip, cette commande n'est pas insérée dans le menu;
    elle doit être tapée directement dans l'url
    """
    promotions = Promotion.objects.all()
    #print promotions
    c = AppliedStudiesPlan.objects.all()
    c.delete()
    for promotion in promotions:
        #print promotion
        pt = TheoricStudiesPlan.objects.filter(formation_id = promotion.formation_id)
        for p in pt:
            AppliedStudiesPlan(promotion_id = promotion.id,
                               content_id = p.content_id,
                               teacher_id = None,
                               teacher_period = p.teacher_period,
                               student_period = p.student_period).save()
    return HttpResponseRedirect('/promotions')


def remaind(request):
    """
    Solde des cours à attribuer
    """
    c = AppliedStudiesPlan.objects.filter(teacher_id = None).order_by('content','promotion')
    teachers = Teacher.objects.all()
    return render(request, 'remaind.html', {'courses': c,
                                            'teachers': teachers,
                                            'courses_number': len(c)})


def repart_by_formation(request):
    courses = AppliedStudiesPlan.objects.filter(promotion__formation__name = '2FE', teacher__code = 'SBD')
    print courses
    
    return 


def supervision(request):
    """
    Répartit les suivis expérientiels entre les profs de la
    classe en fonction du pourcentage d'enseignement dans la classe
    """
    Supervision.objects.all().delete()
    promotions = Promotion.objects.all()
    for promotion in promotions:
        courses = AppliedStudiesPlan.objects.filter(promotion_id=promotion.id)
        teachers = AppliedStudiesPlan.objects.filter(promotion_id=promotion.id).values('teacher_id').exclude(teacher_id = None).exclude(teacher__able_to_supervision= False)
        teachers.query.group_by = ['teacher_id']
        promotion_total_period = courses.aggregate(Sum('teacher_period'))['teacher_period__sum']
        for t in teachers:
            teacher = get_object_or_404(Teacher,pk=t['teacher_id'])
            teacher_total_period = courses.filter(teacher_id=teacher.id).aggregate(Sum('teacher_period'))['teacher_period__sum']
            students_to_supervise = float(teacher_total_period) / float(promotion_total_period) * promotion.student_number
            students_to_supervise = math.floor(students_to_supervise + 0.5) 
            supervision_period = promotion.formation.supervision_period * students_to_supervise
            #Enregistrement dans le fichier
            s = Supervision.objects.filter(promotion_id=promotion.id, teacher_id=teacher.id)
            if len(s) ==1:
                s[0].teacher_period = supervision_period
                s[0].students_number = students_to_supervise
                s[0].save()
            else:
                ss = Supervision(teacher_id=teacher.id, promotion_id=promotion.id, teacher_period=supervision_period, students_number=students_to_supervise)
                ss.save()
    return HttpResponseRedirect('/promotions/'+str(promotion.id))    

def global_supervision(request):
    """
    Tableau style Excel pour gérer la répartition des suivis expérientiels    
    """
    
    teachers = Teacher.objects.all()
    promotions = Promotion.objects.all()
    #supervisions = Supervision.objects.all()
    tab=[]
    #Titre des colonnes
    row_title_col=[]
    row_title_col.append("Enseignants")
    row_students_number=[]
    row_students_number.append("Effectifs")
    row_current_total=[]
    row_current_total.append('Suivis attribués')
    
    for promotion in promotions:
        row_title_col.append(promotion.short_name)
        row_students_number.append(promotion.student_number)
        row_current_total.append(0)
        
    #tab.append(row_title_col)
    #tab.append(row_students_number)
        
    for teacher in teachers:
        t=[]
        t.append(teacher.full_name())
        for promotion in promotions:
            try:
                supervision = Supervision.objects.get(teacher_id=teacher.id, promotion_id=promotion.id)
                if supervision.students_number == 0:
                    t.append(0)
                else:
                    t.append(supervision.students_number)
            except:
                t.append(0)
            row_current_total[row_title_col.index(promotion.short_name)] += int(t[-1])
            
        tab.append(t)
    #tab.append(row_current_total)    
    return render(request, 'global_supervision.html', {'tab':tab, 'promotions':Promotion.objects.all(), 'current_totals':row_current_total})

def supervision_by_promotion(request, pk):
    """
    Le paramètre est optionnel. S'il est absent, la première valeur
    de la table est utilisée.
    """
    data ={}
    data['promotions'] = Promotion.objects.all()
    if pk is None:
        promotion_selected = data['promotions'][0]
    else:
        promotion_selected = get_object_or_404(Promotion, pk=pk)
    data['teachers'] = Teacher.objects.all()
    data['promotion_selected'] = promotion_selected
    data['supervisions'] = Supervision.objects.filter(promotion_id = promotion_selected.id)
    
    return render(request, 'supervision_promotions.html', data)

class UnicodeWriter:
    """
    A CSV writer which will write rows to CSV file 'f',
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        self.writer.writerow([s.encode("utf-8") for s in row])
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)
            
            
def export_teachers(request):

    teachers = Teacher.objects.all()
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="export_teachers.csv"'

    writer = UnicodeWriter(response)
    writer.writerow(['Code', 'Nom', u'Prénom'])
    
    for teacher in teachers:
        writer.writerow([teacher.code, teacher.last_name, teacher.first_name])
    
    return response



def export_controls(request):
    """
    Retourne le nombre de périodes prof et périodes élèves pour chaque classe
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="export_promotions.csv"'
    writer = UnicodeWriter(response)
    promotions = Promotion.objects.all()
    
    writer.writerow([u'Classe', u'Pér. ens.', u'Pér. élève'])
    for promotion in promotions:
        teacher_periods = AppliedStudiesPlan.objects.filter(promotion_id=promotion.id).aggregate(Sum('teacher_period'))['teacher_period__sum']
        student_periods = AppliedStudiesPlan.objects.filter(promotion_id=promotion.id).aggregate(Sum('student_period'))['student_period__sum']
        writer.writerow([promotion.name, '%d' % teacher_periods, '%d' % student_periods])
        
    return response



"""    
Appels AJAX  ************************************************************
"""
def update_courses(request, pk_course, pk_teacher):

    def getCharge(teacher):
        total = teacher.total()
        data = {'result':'OK',
                'id': teacher.id,
                'name':teacher.full_name(),
                'teaching': total['teaching'],
                'mission': total['mission'],
                'supervision': total['supervision'],
                'others': total['others'],
                'total': total['total'],
                'ept': total['ept'],
                'gap': total['gap'],}
        return data


    course = AppliedStudiesPlan.objects.get(pk=pk_course)
    if course.teacher_id is None:
        old_teacher_id = 0
    else:
        old_teacher_id = course.teacher_id
    if pk_teacher == '0':
        course.teacher_id = None
    else:
        course.teacher_id = pk_teacher
    course.save()

    myList = []
    if old_teacher_id > 0:
        myList.append(getCharge(Teacher.objects.get(pk=old_teacher_id)))
        #myList.append(Teacher.objects.get(pk=old_teacher_id))
    if not int(pk_teacher) == 0:
        myList.append(getCharge(Teacher.objects.get(pk=pk_teacher)))
        #myList.append(Teacher.objects.get(pk=pk_teacher))
    return HttpResponse(json.dumps(myList), content_type="application/json")


def supervision_add(request, pk):
    supervision = get_object_or_404(Supervision, pk=pk)
    supervision.students_number += 1
    supervision.teacher_period += supervision.promotion.formation.supervision_period
    supervision.save()
    total = supervision.teacher.total()
    myList = []
    result = {'result':'OK',
            'id': supervision.teacher_id,
            'name':supervision.teacher.full_name(),
            'teaching': total['teaching'],
            'mission': total['mission'],
            'supervision': total['supervision'],
            'others': total['others'],
            'total': total['total'],
            'ept': total['ept'],
            'gap': total['gap'],
            'new_students_number': supervision.students_number}
    myList.append(result)
    return HttpResponse(json.dumps(myList), content_type="application(json")


def supervision_minus(request, pk):
    supervision = get_object_or_404(Supervision, pk=pk)
    supervision.students_number -= 1
    supervision.teacher_period -= supervision.promotion.formation.supervision_period
    if supervision.students_number < 0:
        supervision.students_number = 0
    if supervision.teacher_period < 0:
        supervision.teacher_period = 0
    supervision.save()
    total = supervision.teacher.total()
    myList=[]
    result = {'result':'OK',
            'id': supervision.teacher_id,
            'name':supervision.teacher.full_name(),
            'teaching': total['teaching'],
            'mission': total['mission'],
            'supervision': total['supervision'],
            'others': total['others'],
            'total': total['total'],
            'ept': total['ept'],
            'gap': total['gap'],
            'new_students_number': supervision.students_number}
    myList.append(result)
    return HttpResponse(json.dumps(myList), content_type="application(json")  

  