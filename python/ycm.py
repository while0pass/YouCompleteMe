#!/usr/bin/env python
#
# Copyright (C) 2011, 2012  Strahinja Val Markovic  <val@markovic.io>
#
# This file is part of YouCompleteMe.
#
# YouCompleteMe is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# YouCompleteMe is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with YouCompleteMe.  If not, see <http://www.gnu.org/licenses/>.

import vimsupport
import imp
import vim
import utils
import os
import sys
from completers.all.identifier_completer import IdentifierCompleter

FILETYPE_SPECIFIC_COMPLETION_TO_DISABLE = vim.eval(
  'g:ycm_filetype_specific_completion_to_disable' )


class YouCompleteMe( object ):
  def __init__( self ):
    self.identcomp = IdentifierCompleter()
    self.filetype_completers = {}


  def GetIdentifierCompleter( self ):
    return self.identcomp


  def GetFiletypeCompleterForCurrentFile( self ):
    filetype = vimsupport.CurrentFiletype()
    try:
      return self.filetype_completers[ filetype ]
    except KeyError:
      pass

    module_path = _PathToFiletypeCompleterPluginLoader( filetype )

    completer = None
    supported_filetypes = [ filetype ]
    if os.path.exists( module_path ):

      sys.path.append( os.path.dirname( module_path ) )
      module = imp.load_source( filetype, module_path )
      del sys.path[ -1 ]

      completer = module.GetCompleter()
      if completer:
        supported_filetypes.extend( completer.SupportedFiletypes() )

    for supported_filetype in supported_filetypes:
      self.filetype_completers[ supported_filetype ] = completer
    return completer


  def ShouldUseIdentifierCompleter( self, start_column ):
    return self.identcomp.ShouldUseNow( start_column )


  def ShouldUseFiletypeCompleter( self, start_column ):
    if self.FiletypeCompletionEnabledForCurrentFile():
      return self.GetFiletypeCompleterForCurrentFile().ShouldUseNow(
        start_column )
    return False


  def FiletypeCompletionAvailableForFile( self ):
    return bool( self.GetFiletypeCompleterForCurrentFile() )


  def FiletypeCompletionEnabledForCurrentFile( self ):
    return ( vimsupport.CurrentFiletype() not in
                FILETYPE_SPECIFIC_COMPLETION_TO_DISABLE and
             self.FiletypeCompletionAvailableForFile() )


  def OnFileReadyToParse( self ):
    self.identcomp.OnFileReadyToParse()

    if self.FiletypeCompletionEnabledForCurrentFile():
      self.GetFiletypeCompleterForCurrentFile().OnFileReadyToParse()


  def OnInsertLeave( self ):
    self.identcomp.OnInsertLeave()

    if self.FiletypeCompletionEnabledForCurrentFile():
      self.GetFiletypeCompleterForCurrentFile().OnInsertLeave()


  def DiagnosticsForCurrentFileReady( self ):
    if self.FiletypeCompletionEnabledForCurrentFile():
      return self.GetFiletypeCompleterForCurrentFile().DiagnosticsForCurrentFileReady()
    return False


  def GetDiagnosticsForCurrentFile( self ):
    if self.FiletypeCompletionEnabledForCurrentFile():
      return self.GetFiletypeCompleterForCurrentFile().GetDiagnosticsForCurrentFile()
    return []


  def ShowDetailedDiagnostic( self ):
    if self.FiletypeCompletionEnabledForCurrentFile():
      return self.GetFiletypeCompleterForCurrentFile().ShowDetailedDiagnostic()


  def OnCurrentIdentifierFinished( self ):
    self.identcomp.OnCurrentIdentifierFinished()

    if self.FiletypeCompletionEnabledForCurrentFile():
      self.GetFiletypeCompleterForCurrentFile().OnCurrentIdentifierFinished()


def _PathToCompletersFolder():
  dir_of_current_script = os.path.dirname( os.path.abspath( __file__ ) )
  return os.path.join( dir_of_current_script, 'completers' )


def _PathToFiletypeCompleterPluginLoader( filetype ):
  return os.path.join( _PathToCompletersFolder(), filetype, 'hook.py' )


def CompletionStartColumn():
  """Returns the 0-based index where the completion string should start. So if
  the user enters:
    foo.bar^
  with the cursor being at the location of the caret, then the starting column
  would be the index of the letter 'b'.
  """

  line = vim.current.line
  start_column = vimsupport.CurrentColumn()

  while start_column > 0 and utils.IsIdentifierChar( line[ start_column - 1 ] ):
    start_column -= 1
  return start_column


def CurrentIdentifierFinished():
  current_column = vimsupport.CurrentColumn()
  previous_char_index = current_column - 1
  if previous_char_index < 0:
    return True
  line = vim.current.line
  try:
    previous_char = line[ previous_char_index ]
  except IndexError:
    return False

  if utils.IsIdentifierChar( previous_char ):
    return False

  if ( not utils.IsIdentifierChar( previous_char ) and
       previous_char_index > 0 and
       utils.IsIdentifierChar( line[ previous_char_index - 1 ] ) ):
    return True
  else:
    return line[ : current_column ].isspace()


