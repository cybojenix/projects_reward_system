from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.forms import ModelForm
from django.shortcuts import redirect, render
from django.template import RequestContext

from student import utils
from student.models import Student, Points


class CreateStudentForm(ModelForm):
    class Meta:
        model = Student
        fields = ['first_name', 'last_name', 'year_group', 'tutor_group']


class AssignPointForm(ModelForm):
    class Meta:
        model = Points
        fields = ['points', 'reason', 'added']


@login_required()
def create_student(request):
    if not request.user.is_staff:
        return redirect('/')
    if request.method == 'POST':  # If the form has been submitted
        form = CreateStudentForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            year_group = form.cleaned_data['year_group']
            tutor_group = form.cleaned_data['tutor_group']
            student = utils.create_student_object(
                first_name,
                last_name,
                year_group,
                tutor_group)
            student.save()
            form = CreateStudentForm()
            return render(request, "student/create.html", {
                'success': " ".join([student.first_name, student.last_name]),
                'form': form, },
                context_instance=RequestContext(request))
    else:
        form = CreateStudentForm()  # empty form
    return render(request, 'student/create.html', {
        'form': form,
    }, context_instance=RequestContext(request))


@login_required()
def view_students(request):
    query = request.GET.get('q')
    page = request.GET.get('page')
    q_without_page = request.GET.copy()
    if 'page' in q_without_page:
        del q_without_page['page']
    if query:
        if ' ' in query:
            query = query.split(' ')
            student_list = Student.objects.filter(Q(first_name__icontains=query[0]),
                                                  Q(last_name__icontains=query[1]) |
                                                  Q(first_name__icontains=query[1]),
                                                  Q(last_name__icontains=query[0]))
        else:
            student_list = Student.objects.filter(Q(first_name__icontains=query) |
                                                  Q(last_name__icontains=query))
    else:
        student_list = Student.objects.order_by('last_name')
    paginator = Paginator(student_list, 10)
    try:
        students = paginator.page(page)
    except PageNotAnInteger:
        students = paginator.page(1)
    except EmptyPage:
        students = paginator.page(paginator.num_pages)
    context = {'students': students, 'queries': q_without_page}
    return render(request, 'student/student_list.html',
                  context, context_instance=RequestContext(request))


@login_required()
def assign_point(request, student_id):
    try:
        std = Student.objects.get(user_id=student_id)
    except Student.DoesNotExist:
        return redirect('/')
    del std
    if request.method == 'POST':
        form = AssignPointForm(request.POST)
        if form.is_valid():
            points = form.cleaned_data['points']
            reason = form.cleaned_data['reason']
            added = form.cleaned_data['added']
            point = utils.assign_student_point(
                user_id=student_id,
                points=points,
                added=added,
                reason=reason
            )
            print points
            point.save()
            return redirect('/')
    else:
        form = AssignPointForm()
    return render(request, 'student/assign_point.html', {
        'form': form,
        'id': student_id,
    }, context_instance=RequestContext(request))
