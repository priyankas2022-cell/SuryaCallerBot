"use client";

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Activity, Phone, Plus } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useAuth } from '@/lib/auth';

export default function OverviewPage() {
    const router = useRouter();
    const { user, provider } = useAuth();
    const isOSSMode = provider !== 'stack';

    return (
        <div className="container mx-auto px-4 py-8">
            <div className="max-w-4xl mx-auto">
                {/* Welcome Card */}
                <Card className="mb-8">
                    <CardHeader>
                        <CardTitle className="text-3xl">
                            {isOSSMode ? (
                                "Welcome to Smart AI Caller"
                            ) : (
                                `Welcome${user?.displayName ? `, ${user.displayName.split(' ')[0]}` : ''}!`
                            )}
                        </CardTitle>
                        <CardDescription className="text-lg mt-2">
                            Smart AI Caller is an AI-powered telephony and voice automation platform developed and designed to streamline intelligent calling workflows and customer interactions.
                        </CardDescription>
                    </CardHeader>
                    <CardContent />
                </Card>

                {/* Quick Actions */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                    <Card>
                        <CardHeader>
                            <div className="p-2 w-fit rounded-lg bg-primary/10 text-primary mb-2">
                                <Plus className="h-6 w-6" />
                            </div>
                            <CardTitle>Create and Manage Agents</CardTitle>
                            <CardDescription>
                                Build powerful AI Voice Agents with our visual editor
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            <Button asChild className="bg-yellow-400 hover:bg-yellow-500 text-black">
                                <Link href="/workflow">
                                    Go to Agents
                                </Link>
                            </Button>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader>
                            <div className="p-2 w-fit rounded-lg bg-primary/10 text-primary mb-2">
                                <Activity className="h-6 w-6" />
                            </div>
                            <CardTitle>Configure Services</CardTitle>
                            <CardDescription>
                                Set up your AI services like LLM, TTS, and STT providers
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            <Button asChild className="bg-yellow-400 hover:bg-yellow-500 text-black">
                                <Link href="/model-configurations">
                                    Configure Models
                                </Link>
                            </Button>
                        </CardContent>
                    </Card>
                </div>

                {/* Resources Section */}
                <Card>
                    <CardHeader>
                        <CardTitle>Resources & Support</CardTitle>
                        <CardDescription>
                            Get help and learn more about Smart AI Caller
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="flex flex-wrap gap-4">
                            <Button asChild className="bg-yellow-400 hover:bg-yellow-500 text-black">
                                <a
                                    href="https://docs.suryacaller.com"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                >
                                    Documentation
                                </a>
                            </Button>
                            <Button asChild className="bg-yellow-400 hover:bg-yellow-500 text-black">
                                <a
                                    href="https://github.com/suryacaller-hq/suryacaller/issues"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                >
                                    Report an Issue
                                </a>
                            </Button>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
