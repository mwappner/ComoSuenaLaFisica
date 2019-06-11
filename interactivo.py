# -- coding: utf-8 --
"""
Created on Sat Jun  8 00:37:29 2019

@author: Marcos
"""

#sr, duration, freq = 32000, 10, 280
#time = np.linspace(0, duration, duration * sr, endpoint=False)
#seno = (2**15-1) * np.sin(time * 2 * np.pi * freq) / 4
#seno = seno.astype(np.int16)
#
#ply_this = sa.play_buffer(seno, 1, 2, sr)
#ply_this.wait_done()

#%%
import matplotlib
matplotlib.use('TkAgg')
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator

import tkinter as tk
from tkinter import ttk

from itertools import chain
import simpleaudio as sa

valores_que_cambian = 'fs', 'duracion', 'frec', 'volumen'

class Plot(Figure):
    
    def __setattr__(self, name, value):
        '''Me aseguro de que cuando uno de los valores de la curva cambie,
        self.changed también cambie.'''
        super().__setattr__(name, value)
        if name in valores_que_cambian:
            self.changed = True
               
    def __init__(self, vars_amp, vars_fas, fs=32000, duracion=1, frec=150, volumen=100, *a, **k):
        
        #variables de la curva
        self.amplis = vars_amp
        self.fases = vars_fas
        
        #parámetros del sonido
        self.fs = fs #Hz
        self.duracion  = duracion #segundos
        self.frec = frec #Hz
        self.volumen = volumen #en %
        self._pers_shown = 1

        super().__init__(*a, **k)
        self.reset() #poner los valores iniciales
        self.init_plot() 

    @property
    def pers_shown(self):
        return self._pers_shown
    @pers_shown.setter
    def pers_shown(self, value):
        value = int(np.clip(value, 1, 10)) #entro 0 y 10
        self._pers_shown = value
        self.t = np.linspace(0, value, 800)
        self.update()

    def init_plot(self):
        '''Inicializa la fig con los dos plots. Linquea la modificación de los 
        valores de los parámetros a ala actualización del plot.''' 
        self.subplots(1,2)
        self.barras()
        self.curva()
        for v in chain(self.amplis, self.fases):
            v.trace('w', self.update)

    def put_canvas(self, master, mode='grid', *args, **kwargs):
        '''Pone la imagen en la ventana.'''
        self.canvas = FigureCanvasTkAgg(self, master=master)

        if mode.lower()=='grid':
            self.canvas.get_tk_widget().grid(*args, **kwargs)
        elif mode.lower()=='pack':
            self.canvas.get_tk_widget().pack(*args, **kwargs)
        elif mode.lower()=='place':    
            self.canvas.get_tk_widget().place(*args, **kwargs)  
        else:
            raise ValueError("Mode must be 'grid', 'place', or 'pack'.") 
        self.canvas.draw()

    def barras(self):
        '''Gráfico de barras de las amplitudes.'''
        ax = self.axes[0]
        x = list(range(len(self.amplis)))
        y = [v.get() for v in self.amplis]
        self.bars = ax.bar(x,y)
        ax.set_xlabel('# Armónico')
        ax.set_ylabel('Amplitud [u.a.]')
        ax.set_ylim(0,105)
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))

    def senos(self, t, frec=1):
        '''Genero la suma de senos normalizada.'''
        senito = lambda amp, fas, i: amp * np.sin(np.pi * 2 * (i+1) * t * frec + fas * 2 * np.pi / 360)
        senos = sum([senito(a.get(), f.get(), i) for i, (a,f) in enumerate(zip(self.amplis, self.fases))])
        if np.abs(senos).max==0:
            return np.zeros(senos.shape)
        else:
            return senos/np.abs(senos).max()

    def curva(self):
        '''Gráfico de la curva de un período del sonido.'''
        ax = self.axes[1]
        self.t = np.linspace(0, self.pers_shown, 800)
        self.l = ax.plot(self.t, self.senos(self.t))[0] #el [0] para tomar la línea del plot
        ax.set_xticks([],[]) #sin ticks en los ejes
        ax.set_yticks([],[]) #sin ticks en los ejes
        ax.set_xlabel('Período [aprox. {}ms]'.format(1000/self.fs))
        
    def update(self, *a): #mejorar tomando índice cambiado (acelerar)
        '''Actualizo gráficos.'''
        for b, v in zip(self.bars, self.amplis):
            b.set_height(v.get())
        self.l.set_ydata(self.senos(self.t))
        self.canvas.draw()
        self.changed = True
        
    def reset(self):
        '''Reinicio todos los valores de los parámetros.'''
        for v in chain(self.amplis[1:], self.fases):
            v.set(0)
        self.amplis[0].set(100)
        self.changed = True
        
    def create_sound(self):
        '''Crea el sonido a reproducir, sólo si hubo cambios desde la última vez.'''
        if self.changed:
            tiempo = np.linspace(0, self.duracion, self.duracion * self.fs, endpoint=False)            
            self.sound = self.volumen/100 * (2**15-1) * self.senos(tiempo, self.frec)
            self.sound = self.sound.astype(np.int16)
            self.changed = False
        return self.sound
    
    def play(self):
        self.player = sa.play_buffer(self.create_sound(), 1, 2, self.fs)
        
    def stop(self):
        self.player.stop()
    
    def call_or_place(self, new, old):
        '''Reemplaza los valores en old por los dados en new, que puede ser un
        iterable (no un generador!), o un callable que cree los nuevos valores.'''
        if callable(new):
            for i, o in enumerate(old):
                o.set(new(i))
        else:
            if len(old)>len(new):
                new += [0] * (len(old)-len(new))
            for o, n in zip(old, new):
                o.set(n)
    
    def set_mode(self, amplitudes, fases=[]):
        self.call_or_place(amplitudes, self.amplis)
        self.call_or_place(fases, self.fases)

#=====================================
###### Defino modos preseteados#######
#=====================================

def random():
    func = lambda i: np.random.randint(0,100)
    p.set_mode(func, func)

def unosobreene():
    amplis_func = lambda i: 100/(1+i) #amplitud máxima es 100, arranca en i=0
    p.set_mode(amplis_func) #como todas las fases son 0, no ahce falta pasarlo

def cuadrada():
    def amplis_func(i):
        i += 1 #OJO! El programa arranca en i=0, pero la serie armónica en i=1
        if i%2: #sólo los impares
            return 100/(i) #amplitud máxima es 100...
        else:
            return 0
    p.set_mode(amplis_func)

def triangular():
    def amplis_func(i):
        i += 1 #OJO! El programa arranca en i=0, pero la serie armónica en i=1
        if i%2: #sólo los impares
            return 100/(i**2) #amplitud máxima es 100...
        else:
            return 0
        
    def fases_func(i):
        i += 1
        if not (i+1)/2%2: #los de índice 3, 7, 11, 15, ...
            return 180
        else:
            return 0
    p.set_mode(amplis_func, fases_func)

def sawtooth():
    pass

def violin():
    pass

def flauta():
    pass

def trompeta():
    pass

def ejemplo():
    amplitudes = [100, 90, 45, 32, 55, 32, 57, 31, 11]
    fases = [0, 10, 25, 35, 100, 10]
    p.set_mode(amplitudes, fases)

modos = {'cuadrada':cuadrada,
         'triangular':triangular,
         'sawtooth':sawtooth,
         'violín':violin,
         'flauta':flauta,
         'trompeta':trompeta,
         '1/n':unosobreene,
         'ejemplo':ejemplo}

def switcher(*a):
    modos[cb.get()]()
  
#==========================================
###### Defino cosas para la interfaz#######
#==========================================

def makeslider(master, span, name, var):
    '''Crea un slider vertical con un título arriba y un spinbox abajo. El spinbox y el slider 
    están ligados al mism valor. Mete todo en un tk.Frame.
    Toma el padre de todo esto, el rango de valores, el nombre y la variable que modifican.'''
    frame = tk.Frame(master=master)
    tk.Label(master=frame, text=name).pack()
    tk.Scale(master=frame, from_=span[1], to=span[0], sliderlength=12, width=13, variable=var).pack()
    tk.Spinbox(master=frame, from_=span[0], to=span[1], width=3 , textvariable=var, wrap=True).pack()
    return frame


def makeone(master, name, ind):
    '''Crea un toolbar que con dos unidades creadas por makeslider que corresponden a amplitud
    y fase. Mete la dos en un tk.Frame y les da un nombre.
    Toma ek padre de todo esto, el nombre y el índice de la variable.'''
    toolbar = tk.Frame(master=master)
    
    titulo = tk.Frame(master=toolbar, relief=tk.RIDGE, padx=3, pady=2, borderwidth=1)
    tk.Label(master=titulo, text=name).pack(fill=tk.X)
    
    botones = tk.Frame(master=toolbar, relief=tk.RIDGE, padx=3, pady=2, borderwidth=1)
    makeslider(botones, (0,100), 'Ampli', vars_amp[ind]).pack(fill=tk.X)
    makeslider(botones, (0,360), 'Fase', vars_fas[ind]).pack(fill=tk.X)
    
    titulo.pack(fill=tk.X)
    botones.pack(fill=tk.X)
    return toolbar


def paramvar(paramname, dtype='int'):
    if dtype=='int':
        var = tk.IntVar()
    elif dtype=='double':
        var = tk.DoubleVar()
    elif dtype=='str':
        var = tk.StringVar()
    elif dtype=='bool':
        var = tk.BooleanVar()
    else:
        raise ValueError(
                "dtype must be one of ('int', 'double', 'str', 'bool'), but was '{}'".format(dtype))
        
    #Intenta poner el valor existente como inicial. Si no hay pone cero
    var.set(getattr(p, paramname, 0))
    var.trace('w', lambda *a: setattr(p, paramname, var.get()))
    return var
    

def makeparam(master, name, unit, paramname, span=[0,100], dtype='int'):
    frame = tk.Frame(master=master)
    tk.Label(master=frame, text=name).grid(columnspan=2)
    tk.Spinbox(master=frame, textvariable=paramvar(paramname, dtype),
               from_=span[0], to=span[1], width=6).grid(row=1, column=0)
    tk.Label(master=frame, text=unit).grid(row=1, column=1)
    return frame

#=============================
###### Creo la interfaz#######
#=============================

#La ventana grande
root = tk.Tk()
#root.geometry('350x200')

#Variables que van a tener las funciones y que los botones modifican
cant = 20
vars_amp = [tk.DoubleVar() for _ in range(cant)]
vars_fas = [tk.DoubleVar() for _ in range(cant)]

#Pongo gráfico
p = Plot(vars_amp, vars_fas)
p.put_canvas(root, 'grid', row=0, column=0, columnspan=cant, sticky='ew')

#Hago botoneras de armónicos
nombres = ['Modo {}'.format(i) for i in range(cant)]
for i, n in enumerate(nombres):
    makeone(root, n, i).grid(row=1, column=i)

###Botonera de acciones###
botonera = tk.Frame(master=root)
botonera.grid(row=0, column=cant+1, rowspan=2, padx=10)

#Parámetros
botonera_params = tk.Frame(master=botonera, relief=tk.RIDGE, padx=3, pady=2, borderwidth=1)
botonera_params.pack(fill=tk.X, pady=10)
makeparam(botonera_params, 'Frecuencia', 'Hz', 'frec', span=[0, 22000]).pack()
makeparam(botonera_params, 'Duración', 'seg', 'duracion', dtype='double').pack()
makeparam(botonera_params, 'Frecuencia\nde sampleo', 'Hz', 'fs', span=[0,44200]).pack(pady=20)
makeparam(botonera_params, 'Períodos', '', 'pers_shown', span=[1,10]).pack()

#Play
botonera_play = tk.Frame(master=botonera, relief=tk.RIDGE, padx=3, pady=2, borderwidth=1)
botonera_play.pack(fill=tk.X, pady=10)
contenedor = tk.Frame(master=botonera_play)
contenedor.pack(pady=5)

tam = dict(height=1, width=1, padx=6)
tk.Button(master=contenedor, text='⏵', command=p.play, **tam).grid(row=0, column=0, padx=2)
tk.Button(master=contenedor, text='||', command=p.stop, **tam).grid(row=0, column=1, padx=2)
makeslider(contenedor, (0,100), 'Volumen', paramvar('volumen')).grid(row=1, columnspan=2)

#Presets
botonera_presets = tk.Frame(master=botonera, relief=tk.RIDGE, padx=3, pady=2, borderwidth=1)
botonera_presets.pack(fill=tk.X, pady=10)

tk.Button(master=botonera_presets, text='Random!', command=random).pack(fill=tk.X, pady=10)
tk.Button(master=botonera_presets, text='Reset', command=p.reset).pack(fill=tk.X, pady=10)

tk.Label(master=botonera_presets, text='Modo:').pack(fill=tk.X)
cb = ttk.Combobox(botonera_presets, state='readonly', values=list(modos.keys()), 
                  width=max([len(m) for m in modos.keys()]))
cb.bind("<<ComboboxSelected>>", switcher)
cb.pack(fill=tk.X)
tk.Button(master=botonera_presets, text='Apply!', command=switcher).pack(fill=tk.X, pady=10)

tk.Button(master=botonera, text='Guardar?', state=tk.DISABLED).pack(fill=tk.X, pady=10)



root.mainloop()
