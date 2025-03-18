'use client';

import { createClient } from "@/utils/supabase/client";
import { useState, useEffect } from 'react';

// Move TranscriptModal to be a more complete client component
function TranscriptModal({ onShowTranscript }: { onShowTranscript: (transcript: string) => void }) {
  return (
    <dialog id="transcript-modal" className="rounded-lg p-4 w-full max-w-2xl">
      <div id="transcript-content" className="mb-4"></div>
      <form method="dialog" className="text-right">
        <button className="bg-blue-500 text-white px-4 py-2 rounded">Close</button>
      </form>
    </dialog>
  );
}

// Add PatientInfoModal component
function PatientInfoModal({ onShowPatientInfo }: { onShowPatientInfo: (patientInfo: any) => void }) {
  return (
    <dialog id="patient-info-modal" className="rounded-lg p-4 w-full max-w-2xl">
      <div id="patient-info-content" className="mb-4">
        <h2 className="text-xl font-bold mb-4">Patient Information</h2>
        <div className="space-y-2">
          <div id="patient-details"></div>
        </div>
      </div>
      <form method="dialog" className="text-right">
        <button className="bg-blue-500 text-white px-4 py-2 rounded">Close</button>
      </form>
    </dialog>
  );
}

// Remove the async from the default export since we're making it a client component
export default function Home() {
  const [callHistory, setCallHistory] = useState<any[]>([]);
  const supabase = createClient();

  // Move data fetching to useEffect
  useEffect(() => {
    const fetchData = async () => {
      const { data } = await supabase
        .from('AssortHealthChatHistory')
        .select('*')
        .order('created_at', { ascending: false });
      
      if (data) setCallHistory(data);
    };

    fetchData();
  }, []);

  const showTranscript = (transcript: string) => {
    try {
      // Remove the outer quotes and square brackets
      const cleanTranscript = transcript.slice(2, -2);
      
      // Split into individual messages
      const transcriptArray = cleanTranscript.split('", "');

      const messages = transcriptArray
        .map((msg: string) => {
          // Split the message if it contains multiple USER: or AGENT: parts
          const parts = msg.split(/(?=USER:|AGENT:)/);
          
          return parts.map(part => {
            // Extract timestamp and message content
            const timestampMatch = part.match(/\[(.*?)\]/);
            const timestamp = timestampMatch ? timestampMatch[1] : '';
            
            // Check if it's a ChatMessage format
            const chatMessageMatch = part.match(/content='([^']+)'/);
            
            let text;
            if (chatMessageMatch) {
              // For USER messages in ChatMessage format
              text = chatMessageMatch[1]
                .replace(/['"]/g, '')  // Remove quotes
                .replace(/,/g, '')     // Remove all commas
                .replace(/\\n/g, '\n') // Replace escaped newlines
                .trim();
            } else {
              // For AGENT messages or direct format
              text = part
                .replace(/\[.*?\]/, '')  // Remove timestamp
                .replace(/\\n/g, '\n')   // Replace escaped newlines
                .replace(/['"]/g, '')    // Remove quotes
                .replace(/,/g, '')       // Remove all commas
                .split('\n')             // Split by newlines
                .filter(line => line.trim()) // Remove empty lines
                .join('\n')              // Join back with newlines
                .trim();
            }
            
            // Determine if it's an agent message
            const isAgent = part.includes('AGENT:');
            
            // Clean up the text
            text = text.replace(/(AGENT:|USER:)/, '').trim();
            
            return {
              timestamp,
              text,
              isAgent
            };
          });
        })
        .flat(); // Flatten the array of arrays

      const modal = document.getElementById('transcript-modal') as HTMLDialogElement;
      const content = document.getElementById('transcript-content');
      
      if (!modal || !content) return;
      
      content.textContent = '';
      
      messages.forEach((msg) => {
        if (!msg || !msg.text) return;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `flex ${msg.isAgent ? 'justify-start' : 'justify-end'} mb-4`;
        
        const bubbleDiv = document.createElement('div');
        bubbleDiv.className = `${msg.isAgent ? 'bg-gray-100' : 'bg-blue-100'} rounded-lg p-3 max-w-[80%]`;
        
        const timeDiv = document.createElement('div');
        timeDiv.className = 'text-xs text-gray-500 mb-1';
        timeDiv.textContent = msg.timestamp;
        
        const textDiv = document.createElement('div');
        textDiv.className = 'whitespace-pre-wrap';
        textDiv.textContent = msg.text;
        
        bubbleDiv.appendChild(timeDiv);
        bubbleDiv.appendChild(textDiv);
        messageDiv.appendChild(bubbleDiv);
        content.appendChild(messageDiv);
      });
      
      modal.showModal();
    } catch (e) {
      console.error('Error processing transcript:', e);
    }
  };

  const showPatientInfo = (patientInfo: any) => {
    try {
      const modal = document.getElementById('patient-info-modal') as HTMLDialogElement;
      const detailsContainer = document.getElementById('patient-details');
      
      if (!modal || !detailsContainer) return;
      
      // Clear previous content
      detailsContainer.innerHTML = '';
      
      // Create formatted display of patient info
      Object.entries(patientInfo).forEach(([key, value]) => {
        const row = document.createElement('div');
        row.className = 'mb-2';
        row.innerHTML = `
          <span class="font-semibold">${key.replace(/_/g, ' ').charAt(0).toUpperCase() + key.slice(1)}: </span>
          <span>${value}</span>
        `;
        detailsContainer.appendChild(row);
      });
      
      modal.showModal();
    } catch (e) {
      console.error('Error showing patient info:', e);
    }
  };

  return (
    <main className="min-h-screen p-4">
      <header className="mb-8">
        <h1 className="text-3xl font-bold">Shahil's Healthcare Call Logs</h1>
      </header>

      {/* Move modal to client component */}
      <TranscriptModal onShowTranscript={showTranscript} />
      <PatientInfoModal onShowPatientInfo={showPatientInfo} />

      {/* Call History Table */}
      <section className="mt-8">
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Phone Number</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Patient Name</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Patient Details</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Call Transcript</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {callHistory && callHistory.length > 0 ? (
                callHistory.map((call) => {
                  const phoneNumber = call.call_ID.split('_')[1] || 'N/A';
                  const patientName = call.patient_info?.name || 'Unknown';
                  const patientDetails = call.patient_info || 'N/A';
                  return (
                    <tr key={call.id}>
                      <td className="px-6 py-4 whitespace-nowrap">{phoneNumber}</td>
                      <td className="px-6 py-4 whitespace-nowrap">{patientName}</td>
                      <td className="px-6 py-4">
                        <button 
                          onClick={() => showPatientInfo(call.patient_info)}
                          className="text-blue-600 hover:text-blue-800 underline"
                        >
                          View Details
                        </button>
                      </td>
                      <td className="px-6 py-4">
                        <button 
                          onClick={() => showTranscript(call.call_logs)}
                          className="text-blue-600 hover:text-blue-800 underline"
                        >
                          See Transcript
                        </button>
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={3} className="px-6 py-4 text-center text-gray-500">
                    No call history available
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}
