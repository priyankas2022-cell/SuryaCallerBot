'use client';

import { PlusIcon } from 'lucide-react';
import { useRouter } from 'next/navigation';

import { Button } from "@/components/ui/button";

export function CreateWorkflowButton() {
    const router = useRouter();
    const handleClick = () => {
        router.push('/workflow/create');
    };

    return (
        <Button
            onClick={handleClick}
            className="bg-yellow-400 hover:bg-yellow-500 text-black"
        >
            <PlusIcon className="w-4 h-4" />
            Create Agent
        </Button>
    );
}
