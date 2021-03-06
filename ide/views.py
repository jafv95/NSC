from django.shortcuts import render, redirect
from .models import Chain, Configuration, Execution
from django.http import HttpResponse
import json
import urllib.request

def index(request):
	data = {}
	chains = Chain.objects.all()
	if chains:
		totalchains = chains.count()
		dic = {}
		#abc = ["a","b","c","d","e","f","g","h","i","j","k","l","m","n","o","p","q","r","s","t","u","v","w","x","y","z"]
		for x in range(totalchains):
			id = chains[x].id
			name = chains[x].name
			description = chains[x].description
			content = json.loads(chains[x].html)
			size = chains[x].size

			c = {
				'id':id,
				'name':name,
				'description':description,
				'content':content,
				'size':size
			}

			key = id
			d = {key:c}
			dic.update(d)

		data = {"dic":dic, "size":len(dic)}
	else:
		data.clear()
	execution = Execution.objects.all()
	runing = list(execution.filter(state=1))
	data['run'] = runing
	return render(request, 'index.html', data)

def saveChain(request):
	name = request.POST.get('name')
	description = request.POST.get('description')
	content = request.POST.get('html')
	size = request.POST.get('size')
	topo1 = request.POST.get('topo1')
	topo2 = request.POST.get('topo2')
	rFw = request.POST.get('rFw')
	#print("[Controller] name: "+name)
	chain = Chain(name = name, description = description, html = content, size = size)
	chain.save()
	configChain = Configuration(nfsconfig = "{fw:"+rFw+"}" , topology = "Tree,"+topo1+","+topo2, idchain = chain)
	configChain.save()
	return HttpResponse(status=200)

def deleteChain(request):
	ids = request.POST.getlist('id')
	for i in ids:
		Chain.objects.get(id=i).delete()
	return redirect('index')

def run(request):
	ids = request.POST.getlist('chain[]')
	ip = request.POST.get('ip')
	print(ids)
	print(ip)
	def switch(i):
		return {
			'firewall':'cmd fw',
			'loadBalancer':'cmd lb',
			'router':'cmd router'
		}.get(i,i) #if i is a NF, return cmd. Else return chain's id (i).
	for i in ids:
		print(switch(i))
	return HttpResponse(status=200)

def status(request):
	currentURL = request.build_absolute_uri(request.get_full_path())
	ip = request.GET.get('ip','127.0.0.1:8081')
	topo_p1 = request.GET.get('topop1','0')
	topo_p2 = request.GET.get('topop2','0')
	rfw = request.GET.get('rfw','{}')
	rr = request.GET.get('rr','{}')
	rLb = request.GET.get('rLb','{}')
	funcs = request.GET.get('funcs','')
	funcs = funcs.split(',')
	print(funcs)
	fs = ""
	#switchID = request.GET.get('id', '0000')
	for i in funcs:
		if fs != "":
			fs = fs + ","
		#print("i: "+i)
		if i != "firewall" and i != "loadBalancer" and i != "router":
			chain = Chain.objects.get(id=i)
			objs_json = chain.html
			nfs = json.loads(objs_json)
			#print("nfs: ")
			#print(nfs)
			orden = [None]*chain.size
			for pos in nfs:
				#print("pos: " + pos)
				nf = nfs[pos]
				#print("nf: " + nf)
				orden[int(pos)] = nf
			#print("orden")
			#print(orden)
			for f in range(0,len(orden)):	# 0 < f < len(orden)
				if f > 0: 
					fs = fs + ","
				#print("orden["+str(f)+"]: "+orden[f])
				fs = fs + orden[f]
		else:
			fs = fs + i
	#print("fs:")
	#print(fs)
	url = 'http://'+ip+'/launcher?f='+fs+'&tp1='+topo_p1+'&tp2='+topo_p2
	ex = Execution.objects.filter(ip = ip, state = 1)
	#print(len(ex.values()))
	if(len(ex.values()) == 0):
		#print("new")
		e = Execution(nfs = fs, ip = ip, state = 1, url=currentURL)
		e.save()
		return render(request, 'status.html', {'type':'new', 'ip':ip, 'topo_p1':topo_p1, 'topo_p2':topo_p2, 'funcs':fs, 'url':url, 'idExec':e.id, 'rfw':rfw, 'rr':rr, 'rLb':rLb})
	else:
		exe_obj = list(ex)
		return render(request, 'status.html', {'type':'old', 'ip':ip, 'topo_p1':topo_p1, 'topo_p2':topo_p2, 'funcs':fs, 'url':url, 'idExec':exe_obj[0].id, 'rfw':rfw, 'rr':rr, 'rLb':rLb})

def setExecutionStateOff(request):
	id = request.GET.get('idExec','0')
	if(id != '0'):
		exec = Execution.objects.get(id=id)
		exec.state = 0
		exec.save()
		return HttpResponse("off")
	else:
		return HttpResponse("error")