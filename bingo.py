# -*- mode:python; tab-width:4; indent-tabs-mode:t; -*-

# bingo.py
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

from sugar.activity import activity

import sys, os
import subprocess
from path import path
import gtk
import random
import time

#
# initial implementation - solo mode
# bingo generates 4 cards to be played by user (standard Bingo)
# call is automatic by activity
# user clicks on square called 
# next call after fixed interval
# activity recognizes bingo
# if user fails to click on called square - no credit
# if user clicks on wrong square - no credit!
#
#
# future phase: change card per control file
# future phase: caller shares with players on other xos (who get one card)
# option: 'caller' can call using microphone instead of activity.
#
#
# process:
#     initiate game by generating cards
#     distribute cards to user(s)
#     configuration includes: number of seconds between calls
#
#
# set up card as array of 3x3 or 5x5 buttons
# each card has a separate screen
#

config = 'bingo'

class Bingo(activity.Activity):

    def __init__(self, handle):
        activity.Activity.__init__(self, handle)
        self.set_title('Bingo')
        self.connect("destroy", self.quit)

        toolbox = activity.ActivityToolbox(self)
        self.set_toolbox(toolbox)
        toolbox.show()

        playing = True
        self.bingo = False
        solo = True
        self.players = 5
        game = 'classic'
        self.callcnt = 0
        self.call = range(75)
        random.shuffle(self.call)

        # generate cards
        self.cards = []
        for p in range(self.players):
            card = []
            for r in range(5):
                base = r*15
                row = range(15)
                random.shuffle(row)
                for i in range(5):
                    card.append(1+base+row[i])
            self.cards.append(card)

        notebook = self.displaycards(self.cards)
        self.main_screen = gtk.VBox()
        self.main_screen.pack_start(notebook, True, True, 0)
        self.status = gtk.HBox()
        start_button = gtk.Button(stock=gtk.STOCK_APPLY)
        start_button.connect('clicked', self.start_cb)
        start_button.show()
        self.currentcall = gtk.Label("Call")
        self.currentcall.show()
        self.status.add(start_button)
        self.status.add(self.currentcall)
        self.bingostate = gtk.Label('No Bingo')
        self.bingostate.show()
        self.status.add(self.bingostate)
        self.status.show()
        self.main_screen.pack_start(self.status, False, False, 0)
        self.main_screen.show()
        self.set_canvas(self.main_screen)
        self.show_all()
      
    def quit(self, parm):
        gtk.main_quit()

    def start_cb(self, widget, data=None):
        bingo = False
        if self.callcnt > 5:
            #check for bingo
            result = ''
            for i in range(self.players):
                bingo = self.checkcard(i, self.cards[i],self.call, result)
                print 'bingo?', bingo, result
                if bingo:
                   print 'BINGO! Card ', str(i), result
                   self.bingostate.set_text('BINGO! Card ' + str(i) + ' ' + result)
                   break
        if not bingo:            
        #    make next call
            thiscall = self.call[self.callcnt]
            self.callcnt += 1
            if thiscall < 16:
                calltxt ='"B,   ' + str(thiscall) + '"'
            elif thiscall < 31:
                calltxt = '"I,   ' + str(thiscall) + '"'
            elif thiscall < 46:
                calltxt = '"N,   ' + str(thiscall) + '"'
            elif thiscall < 61:
                calltxt = '"G,   ' + str(thiscall) + '"'
            else:
                calltxt = '"O,   ' + str(thiscall) + '"'
            print calltxt
            self.currentcall.set_text(calltxt)
            subprocess.call('espeak ' + calltxt, shell=True)
        else: # game over
            #announce winner
                self.bingostate.set_text('BINGO!')                   
            
     
    def displaycards(self, cards):
        notebook = gtk.Notebook()
        notebook.set_tab_pos(gtk.POS_TOP)
        for i in range(len(cards)):
            card = self.makecard('bingo', i, cards[i])
            card.show()
            label = gtk.Label(str(i+1))
            notebook.append_page(card,label)
        notebook.show()
        return notebook
    
    def makecard(self, config, cardid, card):
        if config == 'bingo':
            labels = []
            labtxt = 'BINGO'
             
            for i in range(5):
                label = gtk.Label(labtxt[i])
                label.show()
                labels.append(label)
 
            buttons = []
            for i in range(25):
                button = gtk.Button(str(card[i]))
                strng = 'card ' + str(cardid) + ': ' + str(card[i])
                button.connect('clicked', self.buttoncb, strng)
                button.show()
                buttons.append(button)

            card = gtk.Table(rows=6, columns=5, homogeneous=True)
            for i in range(5):
                card.attach(labels[i], i, i+1, 0, 1)
            for i in range(5):
                for j in range(5):
                    la = i%5
                    ra = i + 1
                    tr = j + 1
                    tl = j + 2                
                    card.attach(buttons[i*5+j],la,ra,tr,tl)
            return card

    def buttoncb(self, widget, parm):
        print 'click at', parm
        widget.modify_bg(gtk.STATE_NORMAL,gtk.gdk.color_parse('green'))            

    def checkcard(self, player, card, call, result):
        result = result + str(player) + '  c:'
        # check columns
        for i in range(5):
            r = self.checkcolumn(card, i)
            result = result + str(r) + ' '
            print 'checkcolumn', player, i, r
            if r == 5:
                return True
        # check rows
        result = result + ' r:'
        for i in range(5):
            r = self.checkrow(card, i)
            result = result + str(r) + ' '
            print 'checkrow', player, i, r
            if r == 5:
                return True
        # check diagonals
        result = result + ' d:'
        for i in range(2):
            r = self.checkdiagonal(card, i)
            result = result + str(r) + ' '
            print 'checkdiagonal', player, i, r
            if r == 5:
                return True
        self.bingostate.set_text(result)    
        return False

    def checkrow(self,card, i):
        bingo = 0
        for j in range(5):
            if card[i+j*5] in self.call[:self.callcnt]:
                bingo += 1
        return bingo

    def checkcolumn(self,card, i):
        bingo = 0
        for j in range(5):
            if card[j+i*5] in self.call[:self.callcnt]:
                bingo += 1
        return bingo

    def checkdiagonal(self,card, i):
        bingo = 0
        for j in range(5):
            if i < 1:
                if card[j+j*5] in self.call[:self.callcnt] or (j == 2):
                    bingo += 1
            else:
                if card[(4-j)+j*5] in self.call[:self.callcnt] or (j == 2):
                    bingo += 1
                
