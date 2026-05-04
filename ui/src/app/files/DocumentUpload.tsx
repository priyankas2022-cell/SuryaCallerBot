'use client';

import { Upload } from 'lucide-react';
import { useRef, useState } from 'react';
import { toast } from 'sonner';

import {
  getUploadUrlApiV1KnowledgeBaseUploadUrlPost,
  processDocumentApiV1KnowledgeBaseProcessDocumentPost,
} from '@/client/sdk.gen';
import type { DocumentUploadResponseSchema } from '@/client/types.gen';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import logger from '@/lib/logger';

interface DocumentUploadProps {
  onUploadSuccess: () => void;
}

const MAX_FILE_SIZE = 100 * 1024 * 1024; // 100MB

export default function DocumentUpload({ onUploadSuccess }: DocumentUploadProps) {
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadStatusText, setUploadStatusText] = useState('');
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateFile = (file: File): boolean => {
    // Validate file size only — all file types are accepted
    if (file.size > MAX_FILE_SIZE) {
      toast.error(`File size for ${file.name} must be less than 100MB`);
      return false;
    }
    return true;
  };

  const uploadFiles = async (files: File[]) => {
    const validFiles = files.filter(validateFile);
    if (validFiles.length === 0) return;

    setUploading(true);
    setUploadProgress(0);

    let successfulUploads = 0;
    const totalFiles = validFiles.length;

    try {
      for (let i = 0; i < totalFiles; i++) {
        const file = validFiles[i];
        const currentFileProgressBase = (i / totalFiles) * 100;
        const perFileProgressStep = 100 / totalFiles;

        setUploadStatusText(`Uploading ${i + 1} of ${totalFiles}: ${file.name}`);

        // Step 1: Request presigned upload URL
        logger.info('Requesting presigned upload URL for:', file.name);
        const uploadUrlResponse = await getUploadUrlApiV1KnowledgeBaseUploadUrlPost({
          body: {
            filename: file.name,
            mime_type: file.type || 'application/octet-stream',
            custom_metadata: {
              original_filename: file.name,
              uploaded_at: new Date().toISOString(),
            },
          },
        });

        if (uploadUrlResponse.error || !uploadUrlResponse.data) {
          logger.error(`Failed to get upload URL for ${file.name}`);
          toast.error(`Failed to start upload for ${file.name}`);
          continue; // Skip to next file
        }

        const uploadData: DocumentUploadResponseSchema = uploadUrlResponse.data;
        logger.info('Received presigned URL, uploading file...');

        setUploadProgress(currentFileProgressBase + (perFileProgressStep * 0.25));

        // Step 2: Upload file directly to S3/MinIO using PUT
        const uploadResponse = await fetch(uploadData.upload_url, {
          method: 'PUT',
          body: file,
          headers: {
            'Content-Type': file.type || 'application/octet-stream',
          },
        });

        if (!uploadResponse.ok) {
          const errorText = await uploadResponse.text().catch(() => 'Unknown error');
          logger.error('MinIO upload failed:', {
            status: uploadResponse.status,
            statusText: uploadResponse.statusText,
            body: errorText,
            url: uploadData.upload_url,
          });
          toast.error(`Failed to upload ${file.name}`);
          continue; // Skip to next file
        }

        setUploadProgress(currentFileProgressBase + (perFileProgressStep * 0.75));
        logger.info(`File ${file.name} uploaded successfully, triggering processing...`);

        // Step 3: Trigger document processing
        const processResponse = await processDocumentApiV1KnowledgeBaseProcessDocumentPost({
          body: {
            document_uuid: uploadData.document_uuid,
            s3_key: uploadData.s3_key,
          },
        });

        if (processResponse.error) {
          logger.error(`Failed to trigger processing for ${file.name}`);
          toast.error(`Failed to process ${file.name}`);
          continue; // Skip to next file
        }

        successfulUploads++;
        setUploadProgress(currentFileProgressBase + perFileProgressStep);
        logger.info(`Document processing triggered successfully for ${file.name}`);
      }

      if (successfulUploads > 0) {
        toast.success(`Successfully uploaded ${successfulUploads} document${successfulUploads > 1 ? 's' : ''}. Processing started.`);
        onUploadSuccess();
      } else {
        toast.error('Failed to upload any documents.');
      }
    } catch (error) {
      logger.error('Error uploading documents:', error);
      toast.error(error instanceof Error ? error.message : 'Failed to upload documents');
    } finally {
      setUploading(false);
      setUploadProgress(0);
      setUploadStatusText('');
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || []);
    if (files.length > 0) {
      await uploadFiles(files);
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const files = Array.from(e.dataTransfer.files || []);
    if (files.length > 0) {
      await uploadFiles(files);
    }
  };

  const handleButtonClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="space-y-4">
      <input
        ref={fileInputRef}
        type="file"
        onChange={handleFileSelect}
        className="hidden"
        disabled={uploading}
        multiple
      />

      {/* Drag and Drop Area */}
      <div
        className={`
          border-2 border-dashed rounded-lg p-8 text-center transition-colors
          ${dragActive ? 'border-primary bg-primary/5' : 'border-muted-foreground/25'}
          ${uploading ? 'opacity-50 pointer-events-none' : 'cursor-pointer hover:border-primary hover:bg-muted/50'}
        `}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={handleButtonClick}
      >
        <Upload className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
        <p className="text-lg font-medium mb-2">
          {uploading ? 'Uploading...' : 'Drop your documents here'}
        </p>
        <p className="text-sm text-muted-foreground mb-4">
          or click to browse
        </p>
        <p className="text-xs text-muted-foreground">
          Supported: PDF, DOCX, PPTX, XLSX, HTML, MD (rich parsing) + any text file (.php, .py, .js, .json, .csv, etc.) &mdash; Max 100MB
        </p>
      </div>

      {/* Upload Progress */}
      {uploading && (
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span>{uploadStatusText || 'Uploading...'}</span>
            <span>{Math.round(uploadProgress)}%</span>
          </div>
          <Progress value={uploadProgress} />
        </div>
      )}

      {/* Manual Upload Button */}
      <div className="flex justify-center">
        <Button
          type="button"
          variant="outline"
          onClick={handleButtonClick}
          disabled={uploading}
        >
          {uploading ? 'Uploading...' : 'Choose Files'}
        </Button>
      </div>
    </div>
  );
}
