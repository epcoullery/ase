# -*- encoding: utf-8 -*-
from __future__ import unicode_literals
import math

from django.db import models
from django.db.models import Sum
from reportlab.platypus import BaseDocTemplate, SimpleDocTemplate
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm

FULL_TIME_JOB = 2200.0
FULL_TIME_JOB_PERCENT = FULL_TIME_JOB/100.0
EDUC_FACTOR = 2
EDUC_METTINGS = 24
MAX_OTHER_ACTIVITIES = 250


class Todo(models.Model):
    rec_date = models.DateTimeField()
    text = models.CharField(max_length=200, null=False, blank=False)
    ok = models.BooleanField(default=False)
    
    def __unicode__(self):
        if not self.ok:
            return self.text
         
    
# Create your models here.
class Formation(models.Model):
    name = models.CharField(max_length=10)
    supervision_period = models.IntegerField(null=False, default=0, verbose_name='Suivi exp.')

    class Meta:
        verbose_name = 'Formation'
        ordering = ['name']

    def __unicode__(self):
        return self.name

    
class Promotion(models.Model):
    name = models.CharField(max_length=10, verbose_name='Nom')
    formation = models.ForeignKey(Formation)
    student_number = models.IntegerField(null=False,default=0,verbose_name='Effectif')

    class Meta:
        verbose_name = 'Classe'
        ordering = ['name']

    def __unicode__(self):
        return self.name

    def short_name(self):
        foo = self.name.replace('ASE', '')
        return foo.replace(' ', '')
    
    def save(self):
        if self.pk is None:
            super(Promotion, self).save()
            #Créer le plan d'études ppliqués
            pt = TheoricStudiesPlan.objects.filter(formation_id = self.formation_id)
            for p in pt:
                appliedCourse = AppliedStudiesPlan(promotion_id=self.id,
                                                   content_id=p.content_id,
                                                   teacher_id = None,
                                                   teacher_period = p.teacher_period,
                                                   student_period = p.student_period)
                appliedCourse.save()
        else:
            super(Promotion, self).save()


class Content(models.Model):
    """
    Matières d'enseignement
    """
    code = models.CharField(max_length=30, )
    name = models.CharField(max_length=70, blank=True, null=True)

    class Meta:
        verbose_name = 'Matière'
        ordering = ['code', 'name']

    def __unicode__(self):
        return ('%s : %s') % (self.code, self.name)


class Teacher(models.Model):
    """
    Enseignant-e
    """
    code = models.CharField(max_length=10, unique=True)
    first_name = models.CharField(max_length=40, blank=True, null=True, verbose_name='Prénom')
    last_name = models.CharField(max_length=40, blank=True, null=True, verbose_name='Nom')
    activity_rate = models.FloatField(verbose_name='Taux d\'activité')
    extern = models.BooleanField(default=False, verbose_name='Ens. externe')
    able_to_supervision = models.BooleanField(default=True, verbose_name='OK pour suivis expérientiels')

    class Meta:
        verbose_name = "Enseignant"
        ordering = ['last_name']

    def __unicode__(self):
        return '%s %s (%s)' % (self.last_name, self.first_name, self.code)

    def full_name(self):
        return self.last_name + " " + self.first_name

    def __total_teaching(self):
        self.totTeaching =  AppliedStudiesPlan.objects.filter(teacher__id = self.id).aggregate(Sum('teacher_period'))['teacher_period__sum']
        if self.totTeaching is None:
            return 0.0
        else:
            return math.floor(self.totTeaching)

    def __total_mission(self):
        self.totMission = AdminJob.objects.filter(teacher__id=self.id).aggregate(Sum('teacher_period'))['teacher_period__sum']
        if self.totMission is None:
            return 0.0
        else:
            return math.floor(self.totMission)

    def __total_supervision(self):
        self.totSupervision = Supervision.objects.filter(teacher__id=self.id).aggregate(Sum('teacher_period'))['teacher_period__sum']
        if self.totSupervision is None:
            return 0.0
        else:
            return math.floor(self.totSupervision)

    
    def total(self):
        tot_teaching = self.__total_teaching() * EDUC_FACTOR
        if self.extern == True:
            tot_mission = 0
            self.activity_rate = 0.0
        else:
            tot_mission = self.__total_mission() + EDUC_METTINGS # colloques pédagogiques
            
        if self.able_to_supervision == False:
            tot_supervision = 0
        else:
            tot_supervision= self.__total_supervision()    
        total = tot_teaching + tot_mission + tot_supervision
 
        if self.extern == True:
            others = 0
        else:
            #others = int(total/2200.0 * 250.0 + 0.5)
            others = math.floor(total/FULL_TIME_JOB * MAX_OTHER_ACTIVITIES)
        
        return {'teaching': tot_teaching,
                 'mission': tot_mission,
                 'supervision': tot_supervision,
                 'others': others,
                 'total': others + total,
                 'gap': (others + total - int((self.activity_rate * FULL_TIME_JOB_PERCENT))),
                 'ept': (others+total)/FULL_TIME_JOB_PERCENT}

    def __ept(self):
        return (self.total()['total']/FULL_TIME_JOB_PERCENT)

    def __gap(self):
        return (self.total() - int((self.activity_rate * FULL_TIME_JOB_PERCENT)))


class TheoricStudiesPlan(models.Model):
    """
    Plan d'études théorique
    """
    formation = models.ForeignKey(Formation)
    content = models.ForeignKey(Content)
    teacher_period = models.IntegerField()
    student_period = models.IntegerField()

    class Meta:
        verbose_name = 'PlanThéorique'
        ordering =['formation__name','content__code']

    def __unicode__(self):
        return ('%s : %s (%d pér.)') % (self.formation.name, self.content.name, self.teacher_period)


class AppliedStudiesPlan(models.Model):
    """
    Plan d'études appliqué
    """
    promotion = models.ForeignKey(Promotion, verbose_name='Classe')
    content = models.ForeignKey(Content, verbose_name='Matière')
    teacher = models.ForeignKey(Teacher, blank=True, null=True, verbose_name='Enseignant')
    teacher_period = models.IntegerField(verbose_name='Pér. enseignant')
    student_period = models.IntegerField(verbose_name='Pér. élève')

    class Meta:
        verbose_name = 'PlanAppliqué'
        ordering = ['promotion__formation__name', 'promotion__name', 'content__code']

    def __unicode__(self):
        return ('%s : %s (%d pér.) : %s  ') % (self.promotion.name, self.content, self.teacher_period, self.teacher)


class AdminContent(models.Model):
    """
    Type de mandat
    """
    name = models.CharField(max_length=30, unique=True, blank=False, null=False, verbose_name='Motif')

    class Meta:
        verbose_name = 'Type mandat'
        ordering = ['name']

    def __unicode__(self):
        return self.name


class AdminJob(models.Model):
    """
    Mandats appliqués
    """
    content = models.ForeignKey(AdminContent)
    teacher = models.ForeignKey(Teacher)
    teacher_period = models.IntegerField(verbose_name='Période')

    class Meta:
        verbose_name = 'Mandat'

    def __unicode__(self):
        return '%s : %s' % (self.content, self.teacher)


class Supervision(models.Model):
    """
    Suvi expérientiel des stages
    """
    teacher = models.ForeignKey(Teacher, verbose_name='Enseignant-e')
    promotion = models.ForeignKey(Promotion, verbose_name='Classe')
    teacher_period = models.IntegerField(default=0, verbose_name='Pér. enseignant')
    students_number = models.IntegerField(default=0, verbose_name="Nbre de suivis")

    def __unicode__(self):
        return self.teacher.full_name() + " : " + self.promotion.name + " : " + str(self.students_number)
                
    class Meta:
        ordering=['teacher__last_name', 'promotion__name']


class MyDocTemplate(SimpleDocTemplate):
    """
    Document de base pour PDF
    """

    def __init__(self, name, teacher):
        self.PAGE_WIDTH = A4[0]
        self.PAGE_HEIGHT = A4[1]
        self.CENTRE_WIDTH = self.PAGE_WIDTH/2.0
        self.CENTRE_HEIGHT = self.PAGE_HEIGHT/2.0
        BaseDocTemplate.__init__(self,name, pagesize=A4, topMargin=0.5*cm)
        self.fileName = name
        self.teacher = teacher

    def beforePage(self):
        self.canv.saveState()
        self.canv.setFontSize(8)
        self.canv.drawCentredString(self.CENTRE_WIDTH,1*cm,
                                    self.teacher.full_name() +
                                    "   -   Page : " + str(self.canv.getPageNumber()))
        self.canv.restoreState()
