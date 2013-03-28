# -*- encoding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.db.models import Sum
from reportlab.platypus import BaseDocTemplate, SimpleDocTemplate
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm

# Create your models here.
class Formation(models.Model):
    name = models.CharField(max_length=10)
    supervision_period = models.IntegerField(null=False, default=0, verbose_name='Suivi exp.')

    class Meta:
        verbose_name = 'Formation'
        ordering = ['name']

    def __unicode__(self):
        return self.name

    def save(self):
        if self.name in ['1FE', '2FE', '3FE']:
            self.supervision_period = 5
        elif self.name in ['1MP', '2MP', '3MP', '4MP']:
            self.supervision_period = 10
        else:
            self.supervision_period = 0
        super(Formation, self).save()


class Promotion(models.Model):
    name = models.CharField(max_length=10, verbose_name='Nom')
    formation = models.ForeignKey(Formation)
    student_number = models.IntegerField(null=False,default=0,verbose_name='Effectif')

    class Meta:
        verbose_name = 'Classe'
        ordering = ['name']

    def __unicode__(self):
        return self.name

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

    class Meta:
        verbose_name = "Enseignant"
        ordering = ['last_name']

    def __unicode__(self):
        return '%s %s (%s)' % (self.last_name, self.first_name, self.code)

    def full_name(self):
        return self.last_name + " " + self.first_name

    def __total_teaching(self):
        self.totTeaching =  AppliedStudiesPlan.objects.filter(teacher__id = self.id).aggregate(Sum('teacher_period'))
        if self.totTeaching['teacher_period__sum'] is None:
            return 0
        else:
            return int(self.totTeaching['teacher_period__sum'])

    def __total_mission(self):
        self.totMission = AdminJob.objects.filter(teacher__id=self.id).aggregate(Sum('teacher_period'))
        if self.totMission['teacher_period__sum'] is None:
            return 0
        else:
            return int(self.totMission['teacher_period__sum'])

    def __total_supervision(self):
        self.totSupervision = Supervision.objects.filter(teacher__id=self.id).aggregate(Sum('teacher_period'))
        if self.totSupervision['teacher_period__sum'] is None:
            return 0
        else:
            return int(self.totSupervision['teacher_period__sum'])

    def __total_others(self):
        foo = self.total()
        foo = foo + 15*foo/100. # Tâches diverses
        foo = foo + 10*foo/100. # Formation continue/Actualisation des savoirs
        return foo

    def total(self):
        tot_teaching = self.__total_teaching() * 2
        tot_mission = self.__total_mission() + 24 # colloques pédagogiques
        tot_supervision= self.__total_supervision()
        total = tot_teaching + tot_mission + tot_supervision
        others = 0
        others = others + 15*total/100. # Tâches divers
        others = others + 10*total/100. # Actualisation des savoirs
        others = int(others + 0.50) # Arrondi à l'unité supérieure
        return {'teaching': tot_teaching,
                 'mission': tot_mission,
                 'supervision': tot_supervision,
                 'others': others,
                 'total': others + total,
                 'gap': (others + total - int((self.activity_rate * 22.))),
                 'ept': (others+total)/22.}

    def __ept(self):
        return (self.total()['total']/22.)

    def __gap(self):
        return (self.total() - int((self.activity_rate * 22.)))


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

    def __unicode__(self):
        return self.teacher.full_name + " : " + self.promotion.name

    def generate(self):
        Supervision.objects.all().delete()
        teachers = Teacher.objects.all()
        promotions = Promotion.objects.all()
        for teacher in teachers:
            for promotion in promotions:
                s = Supervision()
                s.teacher = teacher
                s.promotion = promotion
                s.save()


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
