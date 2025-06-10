import { useState } from 'react';
import { createFileRoute } from '@tanstack/react-router';
// @ts-ignore: papaparse may not have types installed. Run: npm install --save-dev @types/papaparse
import Papa from 'papaparse';

export const Route = createFileRoute('/')({
  component: App,
});

function parseCSV(file: File, onSuccess: (data: string[][]) => void, onError: (err: string) => void) {
  Papa.parse(file, {
    complete: (result: any) => {
      if (result.errors.length > 0) {
        onError('CSV解析出错，请检查文件格式。');
      } else {
        onSuccess(result.data as string[][]);
      }
    },
    error: () => {
      onError('文件读取失败。');
    },
  });
}

function App() {
  const [expFile, setExpFile] = useState<File | null>(null);
  const [ctrlFile, setCtrlFile] = useState<File | null>(null);
  const [expData, setExpData] = useState<string[][]>([]);
  const [ctrlData, setCtrlData] = useState<string[][]>([]);
  const [result, setResult] = useState<{ columns: string[]; data: any[] } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleExpChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setError(null);
    const file = e.target.files?.[0];
    setExpFile(file || null);
    if (file) {
      parseCSV(file, setExpData, setError);
    } else {
      setExpData([]);
    }
  };
  const handleCtrlChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setError(null);
    const file = e.target.files?.[0];
    setCtrlFile(file || null);
    if (file) {
      parseCSV(file, setCtrlData, setError);
    } else {
      setCtrlData([]);
    }
  };

  const canMatch =
    expFile && ctrlFile &&
    expData.length > 0 &&
    ctrlData.length > 0 &&
    JSON.stringify(expData[0]) === JSON.stringify(ctrlData[0]);

  const handleMatch = async () => {
    if (!canMatch) {
      setError('请先上传表头一致的实验组和对照组CSV文件');
      return;
    }
    setError(null);
    setLoading(true);
    setResult(null);
    try {
      const formData = new FormData();
      formData.append('experiment', expFile!);
      formData.append('control', ctrlFile!);
      const res = await fetch('http://localhost:8000/api/psm', {
        method: 'POST',
        body: formData,
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || '后端服务出错');
      }
      const data = await res.json();
      setResult(data);
    } catch (e: any) {
      setError(e.message || '匹配失败');
    } finally {
      setLoading(false);
    }
  };

  const handleExport = () => {
    if (!result) return;
    const csv = Papa.unparse([result.columns, ...result.data.map((row) => result.columns.map((col) => row[col]))]);
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'matched_control.csv';
    a.click();
    URL.revokeObjectURL(url);
  };

  const renderTable = (data: string[][], title: string) => (
    <div className="mb-6">
      <div className="font-semibold mb-2">{title}</div>
      {data.length > 0 ? (
        <div className="overflow-auto max-h-64 border rounded-lg">
          <table className="min-w-full border-collapse text-sm">
            <thead className="bg-blue-50">
              <tr>
                {data[0].map((header, idx) => (
                  <th key={idx} className="px-3 py-2 border-b font-semibold text-blue-800">{header}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.slice(1, 21).map((row, i) => (
                <tr key={i} className="even:bg-blue-50">
                  {row.map((cell, j) => (
                    <td key={j} className="px-3 py-2 border-b text-gray-700">{cell}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
          {data.length > 21 && <div className="text-xs text-gray-400 p-2">仅预览前20行</div>}
        </div>
      ) : (
        <div className="text-gray-400">未上传</div>
      )}
    </div>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-100 to-blue-300 flex flex-col items-center justify-start py-12">
      <div className="bg-white rounded-xl shadow-lg p-8 w-full max-w-5xl">
        <h1 className="text-2xl font-bold mb-6 text-blue-700">实验组/对照组CSV上传与倾向性得分匹配</h1>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-6">
          <div>
            <label className="block mb-2 font-semibold">实验组CSV</label>
            <input type="file" accept=".csv" onChange={handleExpChange} className="mb-2" />
            {renderTable(expData, '实验组数据预览')}
          </div>
          <div>
            <label className="block mb-2 font-semibold">对照组CSV</label>
            <input type="file" accept=".csv" onChange={handleCtrlChange} className="mb-2" />
            {renderTable(ctrlData, '对照组数据预览')}
          </div>
        </div>
        {expData.length > 0 && ctrlData.length > 0 && JSON.stringify(expData[0]) !== JSON.stringify(ctrlData[0]) && (
          <div className="text-red-500 mb-4">两个文件的表头不一致，无法进行匹配</div>
        )}
        {error && <div className="text-red-500 mb-4">{error}</div>}
        <button
          className={`px-6 py-2 rounded font-bold text-white transition mb-6 ${canMatch ? 'bg-blue-600 hover:bg-blue-700' : 'bg-gray-400 cursor-not-allowed'}`}
          onClick={handleMatch}
          disabled={!canMatch || loading}
        >
          {loading ? '正在匹配...' : '开始倾向性得分匹配'}
        </button>
        {result && (
          <div className="mt-8">
            <div className="flex items-center mb-2">
              <div className="font-semibold text-lg text-blue-700 mr-4">匹配结果（前20行预览）</div>
              <button
                className="ml-auto px-4 py-1 rounded bg-green-500 text-white hover:bg-green-600 text-sm"
                onClick={handleExport}
              >
                导出CSV
              </button>
            </div>
            <div className="overflow-auto max-h-96 border rounded-lg">
              <table className="min-w-full border-collapse text-sm">
                <thead className="bg-blue-50">
                  <tr>
                    {result.columns.map((header, idx) => (
                      <th key={idx} className="px-3 py-2 border-b font-semibold text-blue-800">{header}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {result.data.slice(0, 20).map((row, i) => (
                    <tr key={i} className="even:bg-blue-50">
                      {result.columns.map((col, j) => (
                        <td key={j} className="px-3 py-2 border-b text-gray-700">{row[col]}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
              {result.data.length > 20 && <div className="text-xs text-gray-400 p-2">仅预览前20行</div>}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
